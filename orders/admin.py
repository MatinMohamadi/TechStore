from django.contrib import admin

from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "variant", "quantity", "unit_price", "total_price"]


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ["status", "changed_at", "note"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_number",
        "user",
        "status",
        "total_amount",
        "shipping_cost",
        "final_amount",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["order_number", "user__email"]
    readonly_fields = [
        "order_number",
        "user",
        "total_amount",
        "final_amount",
        "created_at",
    ]
    inlines = [OrderItemInline, OrderStatusHistoryInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["order", "product", "quantity", "unit_price", "total_price"]


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ["order", "status", "changed_at"]
    list_filter = ["status"]
