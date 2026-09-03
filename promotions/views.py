from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Cart

from .models import Coupon
from .serializers import ApplyCouponSerializer


class ApplyCouponView(APIView):
    """
    POST /api/cart/apply-coupon/ — Apply a discount code to the current cart.

    Validates the coupon and stores the calculated discount on the cart.
    The coupon is NOT consumed here — used_count increments only on
    successful payment (in the payment callback).
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ApplyCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"].strip().upper()

        # Find coupon
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response(
                {"error": "Invalid coupon code."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get cart
        from cart.views import get_or_create_cart
        cart = get_or_create_cart(request)

        if not cart.items.exists():
            return Response(
                {"error": "Cart is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate discount
        cart_total = cart.total_price
        try:
            discount = coupon.calculate_discount(cart_total)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save coupon on cart
        cart.coupon = coupon
        cart.discount_amount = discount
        cart.save(update_fields=["coupon", "discount_amount"])

        return Response(
            {
                "coupon_code": coupon.code,
                "discount_type": coupon.discount_type,
                "discount_value": str(coupon.value),
                "cart_total": str(cart_total),
                "discount_amount": str(discount),
                "final_amount": str(cart_total - discount),
            },
            status=status.HTTP_200_OK,
        )


class RemoveCouponView(APIView):
    """
    DELETE /api/cart/apply-coupon/ — Remove coupon from cart.
    """

    permission_classes = [permissions.AllowAny]

    def delete(self, request):
        from cart.views import get_or_create_cart
        cart = get_or_create_cart(request)
        cart.coupon = None
        cart.discount_amount = 0
        cart.save(update_fields=["coupon", "discount_amount"])
        return Response({"message": "Coupon removed."}, status=status.HTTP_200_OK)
