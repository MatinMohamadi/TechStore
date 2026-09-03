from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ["product", "variant", "quantity", "unit_price_snapshot"]


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "session_key", "total_items", "total_price", "updated_at"]
    list_filter = ["created_at"]
    search_fields = ["user__email", "session_key"]
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["cart", "product", "variant", "quantity", "unit_price_snapshot", "total_price"]
    list_filter = ["cart"]
