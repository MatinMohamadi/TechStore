from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id", "order", "gateway", "amount", "status",
            "transaction_ref", "paid_at", "created_at",
        ]
        read_only_fields = fields


class InitiatePaymentSerializer(serializers.Serializer):
    """Request to initiate a payment."""
    order_id = serializers.IntegerField()
    gateway = serializers.ChoiceField(
        choices=Payment.Gateway.choices,
        default=Payment.Gateway.ZARINPAL,
    )
    callback_url = serializers.URLField()


class CallbackSerializer(serializers.Serializer):
    """Zarinpal callback query parameters."""
    authority = serializers.CharField()
    Status = serializers.CharField()
