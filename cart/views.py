from django.db import transaction
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.services import (
    InsufficientStockError,
    get_available_stock,
    release_stock,
    reserve_stock,
)

from .models import Cart, CartItem
from .serializers import (
    AddCartItemSerializer,
    CartItemSerializer,
    CartSerializer,
    UpdateCartItemSerializer,
)


def get_or_create_cart(request):
    """
    Get or create the active cart for the current request.
    - Logged-in user: use user-based cart
    - Guest: use session_key-based cart
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    else:
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
        return cart


@extend_schema_view(
    get=extend_schema(
        summary="View current cart",
        description="Returns the current user's cart (or guest cart via session). Shows items, quantities, prices, and coupon info.",
        tags=["Cart"],
    )
)
class CartView(APIView):
    """GET /api/cart/ — View current cart."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cart = get_or_create_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


@extend_schema_view(
    post=extend_schema(
        summary="Add item to cart",
        description=(
            "Add a product to the current cart. Validates stock availability. "
            "If the product is already in the cart, increments quantity. "
            "Stock is reserved atomically to prevent overselling."
        ),
        tags=["Cart Items"],
        examples=[
            OpenApiExample(
                "Add 2 units of product",
                value={"product_id": 1, "quantity": 2},
            )
        ],
    )
)
class CartItemAddView(APIView):
    """POST /api/cart/items/ — Add item to cart."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        variant_id = serializer.validated_data.get("variant_id")
        quantity = serializer.validated_data["quantity"]

        from catalog.models import Product, ProductVariant

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(pk=variant_id, product=product)
            except ProductVariant.DoesNotExist:
                return Response(
                    {"error": "Variant not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Check stock availability
        available = get_available_stock(product=product, variant=variant)
        if available < quantity:
            return Response(
                {
                    "error": "Insufficient stock.",
                    "available": available,
                    "requested": quantity,
                },
                status=status.HTTP_409_CONFLICT,
            )

        # Reserve stock
        try:
            reserve_stock(product=product, quantity=quantity, variant=variant)
        except InsufficientStockError as e:
            return Response(
                {"error": str(e), "available": e.available, "requested": e.requested},
                status=status.HTTP_409_CONFLICT,
            )

        # Get or create cart
        cart = get_or_create_cart(request)

        # Get or update cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={
                "quantity": quantity,
                "unit_price_snapshot": product.effective_price,
            },
        )
        if not created:
            # Update quantity
            new_qty = cart_item.quantity + quantity
            # Check stock for additional quantity
            if available < new_qty:
                # Release what we just reserved
                release_stock(product=product, quantity=quantity, variant=variant)
                return Response(
                    {"error": "Insufficient stock for requested quantity."},
                    status=status.HTTP_409_CONFLICT,
                )
            cart_item.quantity = new_qty
            cart_item.save()

        return Response(
            CartItemSerializer(cart_item).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


@extend_schema_view(
    patch=extend_schema(
        summary="Update cart item quantity",
        description="Change the quantity of a cart item. Stock is adjusted atomically.",
        tags=["Cart Items"],
    ),
    delete=extend_schema(
        summary="Remove cart item",
        description="Remove an item from the cart. Reserved stock is released.",
        tags=["Cart Items"],
    ),
)
class CartItemDetailView(APIView):
    """PATCH/DELETE /api/cart/items/{id}/ — Update or remove cart item."""

    permission_classes = [permissions.AllowAny]

    def patch(self, request, pk):
        cart = get_or_create_cart(request)
        try:
            cart_item = CartItem.objects.get(pk=pk, cart=cart)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_quantity = serializer.validated_data["quantity"]

        old_quantity = cart_item.quantity
        quantity_diff = new_quantity - old_quantity

        if quantity_diff > 0:
            # Adding more — check stock and reserve
            available = get_available_stock(
                product=cart_item.product, variant=cart_item.variant
            )
            if available < quantity_diff:
                return Response(
                    {"error": "Insufficient stock.", "available": available},
                    status=status.HTTP_409_CONFLICT,
                )
            try:
                reserve_stock(
                    product=cart_item.product,
                    quantity=quantity_diff,
                    variant=cart_item.variant,
                )
            except InsufficientStockError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_409_CONFLICT,
                )
        elif quantity_diff < 0:
            # Reducing — release stock
            release_stock(
                product=cart_item.product,
                quantity=abs(quantity_diff),
                variant=cart_item.variant,
            )

        cart_item.quantity = new_quantity
        cart_item.save()

        return Response(CartItemSerializer(cart_item).data)

    def delete(self, request, pk):
        cart = get_or_create_cart(request)
        try:
            cart_item = CartItem.objects.get(pk=pk, cart=cart)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Release all reserved stock for this item
        release_stock(
            product=cart_item.product,
            quantity=cart_item.quantity,
            variant=cart_item.variant,
        )
        cart_item.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    post=extend_schema(
        summary="Merge guest cart into user cart",
        description=(
            "Called after login to transfer guest cart items to the user's account. "
            "Duplicate products are merged (quantities summed). "
            "Returns the updated user cart."
        ),
        tags=["Cart"],
    )
)
class CartMergeView(APIView):
    """
    POST /api/cart/merge/ — Merge guest cart into user cart after login.

    Called automatically after login or explicitly by the frontend.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        session_key = request.data.get("session_key")
        if not session_key:
            return Response(
                {"error": "session_key is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            guest_cart = Cart.objects.get(session_key=session_key)
        except Cart.DoesNotExist:
            return Response(
                {"error": "Guest cart not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user_cart, _ = Cart.objects.get_or_create(user=request.user)

        with transaction.atomic():
            for guest_item in guest_cart.items.select_related("product", "variant"):
                # Check if same product/variant already in user cart
                existing = CartItem.objects.filter(
                    cart=user_cart,
                    product=guest_item.product,
                    variant=guest_item.variant,
                ).first()

                if existing:
                    # Merge quantities
                    new_qty = existing.quantity + guest_item.quantity
                    available = get_available_stock(
                        product=guest_item.product, variant=guest_item.variant
                    )
                    if available < (new_qty - existing.quantity):
                        # Can't merge all — take what's available
                        add_qty = max(0, available)
                        if add_qty > 0:
                            reserve_stock(
                                product=guest_item.product,
                                quantity=add_qty,
                                variant=guest_item.variant,
                            )
                            existing.quantity += add_qty
                            existing.save()
                    else:
                        reserve_stock(
                            product=guest_item.product,
                            quantity=guest_item.quantity,
                            variant=guest_item.variant,
                        )
                        existing.quantity = new_qty
                        existing.save()
                else:
                    # Move item to user cart (stock already reserved from guest cart)
                    guest_item.cart = user_cart
                    guest_item.save()

            # Delete the guest cart
            guest_cart.delete()

        return Response(
            CartSerializer(user_cart).data,
            status=status.HTTP_200_OK,
        )
