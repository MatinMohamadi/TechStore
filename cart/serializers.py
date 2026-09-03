from rest_framework import serializers

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items with product details."""
    product_title = serializers.CharField(source="product.title", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = [
            "id", "product", "product_title", "product_slug", "product_sku",
            "variant", "quantity", "unit_price_snapshot", "total_price",
        ]
        read_only_fields = ["id", "unit_price_snapshot"]


class CartSerializer(serializers.ModelSerializer):
    """Serializer for the cart with nested items."""
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()
    total_items = serializers.ReadOnlyField()
    coupon_code = serializers.CharField(source="coupon.code", read_only=True, default=None)

    class Meta:
        model = Cart
        fields = [
            "id", "user", "session_key", "items", "total_price",
            "total_items", "coupon", "coupon_code", "discount_amount",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "session_key", "discount_amount", "updated_at"]


class AddCartItemSerializer(serializers.Serializer):
    """Serializer for adding an item to the cart."""
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1, default=1)


class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart item quantity."""
    quantity = serializers.IntegerField(min_value=1)
