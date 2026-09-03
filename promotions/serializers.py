from rest_framework import serializers

from .models import Coupon


class CouponSerializer(serializers.ModelSerializer):
    is_valid_now = serializers.ReadOnlyField()

    class Meta:
        model = Coupon
        fields = [
            "id", "code", "discount_type", "value",
            "min_order_amount", "max_uses", "used_count",
            "valid_from", "valid_to", "is_active", "is_valid_now",
        ]
        read_only_fields = ["id", "used_count"]


class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
