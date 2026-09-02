from django.contrib import admin

from .models import (
    Brand,
    Category,
    Product,
    ProductAttribute,
    ProductAttributeValue,
    ProductImage,
    ProductVariant,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "alt_text", "order", "is_main"]


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1
    fields = ["attribute", "value"]


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ["sku", "attributes", "price_diff", "stock"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent", "order"]
    list_filter = ["parent"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "title", "category", "brand", "base_price",
        "discount_price", "sku", "status", "is_featured",
    ]
    list_filter = ["status", "is_featured", "category", "brand"]
    search_fields = ["title", "sku", "description"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProductImageInline, ProductAttributeValueInline, ProductVariantInline]
    list_editable = ["status", "is_featured"]
    list_per_page = 25


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ["name", "unit"]
    search_fields = ["name"]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ["product", "alt_text", "order", "is_main"]
    list_filter = ["is_main"]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ["product", "sku", "price_diff", "stock"]
    search_fields = ["sku"]
