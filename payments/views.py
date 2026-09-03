import logging

from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from orders.models import Order, OrderStatusHistory

from .gateways import PaymentGatewayError, get_gateway
from .models import Payment
from .serializers import CallbackSerializer, InitiatePaymentSerializer

logger = logging.getLogger("payments")


@extend_schema_view(
    post=extend_schema(
        summary="Initiate payment",
        description=(
            "Create a payment transaction and get a redirect URL to the payment gateway. "
            "Supports Zarinpal (default), IDPay, and Stripe. "
            "The `callback_url` is where the gateway redirects after payment."
        ),
        tags=["Payments"],
        examples=[
            OpenApiExample(
                "Initiate Zarinpal payment",
                value={
                    "order_id": 1,
                    "gateway": "zarinpal",
                    "callback_url": "https://yourdomain.com/payment/callback",
                },
            )
        ],
    )
)
class InitiatePaymentView(APIView):
    """
    POST /api/payments/initiate/ — Create a payment and get redirect URL.

    Flow:
    1. Validate order exists and belongs to user
    2. Create Payment record (pending)
    3. Call gateway to get authority token + payment URL
    4. Return payment_url for frontend redirect
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "payment"

    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data["order_id"]
        gateway_name = serializer.validated_data["gateway"]
        callback_url = serializer.validated_data["callback_url"]

        # Validate order
        try:
            order = Order.objects.get(pk=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if order.status not in (Order.Status.PENDING,):
            return Response(
                {"error": f"Order status is '{order.status}', cannot pay."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for existing successful payment
        existing = Payment.objects.filter(
            order=order, status=Payment.Status.SUCCESS
        ).exists()
        if existing:
            return Response(
                {"error": "Order already paid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create pending payment
        payment = Payment.objects.create(
            order=order,
            gateway=gateway_name,
            amount=order.final_amount,
            status=Payment.Status.PENDING,
        )

        # Call gateway
        try:
            gateway = get_gateway(gateway_name)
            result = gateway.initiate_payment(
                amount=order.final_amount,
                order_id=order.id,
                callback_url=callback_url,
                description=f"TechStore Order #{order.order_number}",
            )
        except PaymentGatewayError as e:
            logger.error(f"Payment initiate failed for order {order.order_number}: {e}")
            payment.status = Payment.Status.FAILED
            payment.gateway_data = {"error": str(e)}
            payment.save(update_fields=["status", "gateway_data"])
            return Response(
                {"error": "Payment gateway error.", "details": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Save authority
        payment.transaction_ref = result["authority"]
        payment.gateway_data = {"authority": result["authority"]}
        payment.save(update_fields=["transaction_ref", "gateway_data"])

        return Response(
            {
                "payment_id": payment.id,
                "payment_url": result["payment_url"],
                "authority": result["authority"],
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        summary="Payment gateway callback",
        description=(
            "Handles the callback from the payment gateway after user completes payment. "
            "If payment is verified successfully, updates order status to `paid` "
            "and sends a confirmation email. This endpoint is called by the gateway, "
            "not by the frontend."
        ),
        tags=["Payments"],
    )
)
class PaymentCallbackView(APIView):
    """
    GET /api/payments/callback/ — Handle payment gateway callback.

    Zarinpal sends: ?Authority=xxx&Status=OK
    Flow:
    1. If Status != OK, mark payment failed
    2. Call gateway verify
    3. On success: update Payment + Order status, create OrderStatusHistory
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        serializer = CallbackSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        authority = serializer.validated_data["authority"]
        gateway_status = serializer.validated_data["Status"]

        # Find the payment by authority
        try:
            payment = Payment.objects.select_related("order").get(
                transaction_ref=authority
            )
        except Payment.DoesNotExist:
            return Response(
                {"error": "Invalid payment reference."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # If gateway reports failure
        if gateway_status != "OK":
            payment.status = Payment.Status.FAILED
            payment.gateway_data = {**payment.gateway_data, "callback_status": gateway_status}
            payment.save(update_fields=["status", "gateway_data"])
            return Response(
                {"status": "failed", "message": "Payment was not completed."},
                status=status.HTTP_200_OK,
            )

        # Verify with gateway
        try:
            gateway = get_gateway(payment.gateway)
            result = gateway.verify_payment(
                authority=authority,
                amount=payment.amount,
            )
        except PaymentGatewayError as e:
            logger.error(f"Payment verify failed for payment {payment.id}: {e}")
            return Response(
                {"error": "Verification failed.", "details": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Update payment based on verification result
        with transaction.atomic():
            if result["success"]:
                payment.status = Payment.Status.SUCCESS
                payment.transaction_ref = result.get("transaction_ref") or authority
                payment.paid_at = timezone.now()
                payment.gateway_data = {
                    **payment.gateway_data,
                    "ref_id": result.get("transaction_ref"),
                    "card_pan": result.get("card_pan"),
                }
                payment.save(update_fields=[
                    "status", "transaction_ref", "paid_at", "gateway_data",
                ])

                # Update order status
                order = payment.order
                order.status = Order.Status.PAID
                order.save(update_fields=["status"])

                # Send order confirmation email (async)
                from notifications.tasks import send_order_confirmation_email
                send_order_confirmation_email.delay(order.id)

                # Create status history
                OrderStatusHistory.objects.create(
                    order=order,
                    status=Order.Status.PAID,
                    note=f"Payment successful. Ref: {result.get('transaction_ref')}",
                )

                # Increment coupon usage (only on successful payment)
                if order.coupon:
                    order.coupon.increment_usage()
            else:
                payment.status = Payment.Status.FAILED
                payment.gateway_data = {
                    **payment.gateway_data,
                    "verify_result": result.get("raw", {}),
                }
                payment.save(update_fields=["status", "gateway_data"])

        return Response(
            {
                "status": payment.status,
                "order_number": payment.order.order_number,
                "transaction_ref": payment.transaction_ref,
                "amount": str(payment.amount),
            },
            status=status.HTTP_200_OK,
        )
