from rest_framework import serializers

from .models import Order, OrderItem, OrderStatusHistory


class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source="product.title", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id", "product", "product_title", "product_sku",
            "variant", "quantity", "unit_price", "total_price",
        ]
        read_only_fields = ["id", "total_price"]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ["id", "status", "changed_at", "note"]
        read_only_fields = fields


class OrderListSerializer(serializers.ModelSerializer):
    """Compact serializer for order listing."""
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "status", "total_amount",
            "discount_amount", "shipping_cost", "final_amount",
            "items_count", "created_at",
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Full order detail with items and status history."""
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "user", "user_email", "status",
            "shipping_address", "total_amount", "discount_amount",
            "shipping_cost", "final_amount", "note", "items",
            "status_history", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "order_number", "user", "status",
            "total_amount", "final_amount", "created_at", "updated_at",
        ]


class CheckoutSerializer(serializers.Serializer):
    """Serializer for checkout request."""
    shipping_address_id = serializers.IntegerField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True, default="")
    shipping_cost = serializers.DecimalField(
        max_digits=12, decimal_places=0, default=0
    )
