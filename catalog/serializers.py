from rest_framework import serializers

from .models import (
    Brand,
    Category,
    Product,
    ProductAttributeValue,
    ProductImage,
    ProductVariant,
)


# ── Category ──────────────────────────────────────────────

class CategoryListSerializer(serializers.ModelSerializer):
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "icon", "order", "children_count"]

    def get_children_count(self, obj):
        return obj.children.count()


class CategoryDetailSerializer(serializers.ModelSerializer):
    children = CategoryListSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "icon", "order", "children"]


# ── Brand ─────────────────────────────────────────────────

class BrandListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "slug", "logo"]


class BrandDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "slug", "logo", "description"]


# ── Product ───────────────────────────────────────────────

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "order", "is_main"]


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source="attribute.name", read_only=True)
    attribute_unit = serializers.CharField(source="attribute.unit", read_only=True)

    class Meta:
        model = ProductAttributeValue
        fields = ["id", "attribute", "attribute_name", "attribute_unit", "value"]


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ["id", "sku", "attributes", "price_diff", "stock"]


class ProductListSerializer(serializers.ModelSerializer):
    """Compact serializer for product listing."""
    category_name = serializers.CharField(source="category.name", read_only=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True, default=None)
    main_image = serializers.SerializerMethodField()
    average_rating = serializers.ReadOnlyField()
    in_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            "id", "title", "slug", "category", "category_name",
            "brand", "brand_name", "base_price", "discount_price",
            "effective_price", "sku", "status", "is_featured",
            "warranty_months", "main_image", "average_rating",
            "in_stock", "created_at",
        ]

    def get_main_image(self, obj):
        img = obj.images.filter(is_main=True).first()
        if img:
            return ProductImageSerializer(img).data
        img = obj.images.first()
        return ProductImageSerializer(img).data if img else None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer with images, attributes, variants."""
    category_name = serializers.CharField(source="category.name", read_only=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True, default=None)
    images = ProductImageSerializer(many=True, read_only=True)
    attribute_values = ProductAttributeValueSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()
    in_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            "id", "title", "slug", "category", "category_name",
            "brand", "brand_name", "description", "base_price",
            "discount_price", "effective_price", "sku", "status",
            "is_featured", "warranty_months", "images",
            "attribute_values", "variants", "average_rating",
            "in_stock", "created_at", "updated_at",
        ]
