from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Address
from cart.models import Cart
from inventory.services import (
    InsufficientStockError,
    confirm_stock_reduction,
    get_available_stock,
    reserve_stock,
)

from .models import Order, OrderItem, OrderStatusHistory
from .serializers import (
    CheckoutSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
)


class CheckoutView(APIView):
    """
    POST /api/orders/checkout/ — Convert current cart into an order.

    Steps:
    1. Validate cart is not empty
    2. Check stock availability for all items
    3. Confirm stock reduction (convert reservation to permanent reduction)
    4. Create Order + OrderItems with price snapshots
    5. Create initial OrderStatusHistory record
    6. Clear the cart
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get user's cart
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {"error": "Your cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_items = list(cart.items.select_related("product", "variant"))
        if not cart_items:
            return Response(
                {"error": "Your cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate shipping address
        shipping_address = None
        address_id = serializer.validated_data.get("shipping_address_id")
        if address_id:
            try:
                shipping_address = Address.objects.get(
                    pk=address_id, user=request.user
                )
            except Address.DoesNotExist:
                return Response(
                    {"error": "Invalid shipping address."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Validate stock for all items
        for item in cart_items:
            available = get_available_stock(
                product=item.product, variant=item.variant
            )
            if available < item.quantity:
                return Response(
                    {
                        "error": f"Insufficient stock for '{item.product.title}'.",
                        "available": available,
                        "requested": item.quantity,
                    },
                    status=status.HTTP_409_CONFLICT,
                )

        # Create order atomically
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                order_number=Order.generate_order_number(),
                shipping_address=shipping_address,
                coupon=cart.coupon,
                discount_amount=cart.discount_amount,
                shipping_cost=serializer.validated_data.get("shipping_cost", 0),
                note=serializer.validated_data.get("note", ""),
            )

            # Create order items and confirm stock reduction
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    quantity=item.quantity,
                    unit_price=item.unit_price_snapshot,
                )
                # Confirm stock reduction (was reserved in cart, now permanently reduced)
                confirm_stock_reduction(
                    product=item.product,
                    quantity=item.quantity,
                    variant=item.variant,
                )

            # Calculate totals
            order.recalculate_totals()

            # Create initial status history
            OrderStatusHistory.objects.create(
                order=order,
                status=Order.Status.PENDING,
                note="Order created.",
            )

            # Clear the cart
            cart.items.all().delete()
            cart.delete()

        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderListView(generics.ListAPIView):
    """GET /api/orders/ — List current user's orders."""

    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderDetailView(generics.RetrieveAPIView):
    """GET /api/orders/{id}/ — Order detail (owner only)."""

    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
