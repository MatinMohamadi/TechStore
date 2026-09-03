from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id", "product", "user", "user_email",
            "rating", "comment", "is_approved", "created_at",
        ]
        read_only_fields = ["id", "user", "is_approved", "created_at"]

    def validate(self, attrs):
        """Ensure user has purchased this product."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            product = attrs.get("product")
            # Check if user has a paid order with this product
            from orders.models import Order, OrderItem
            has_purchased = OrderItem.objects.filter(
                order__user=request.user,
                order__status__in=[Order.Status.PAID, Order.Status.PROCESSING,
                                   Order.Status.SHIPPED, Order.Status.DELIVERED],
                product=product,
            ).exists()
            if not has_purchased:
                raise serializers.ValidationError(
                    "You can only review products you have purchased."
                )

            # Check for existing review
            if Review.objects.filter(user=request.user, product=product).exists():
                raise serializers.ValidationError(
                    "You have already reviewed this product."
                )
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
