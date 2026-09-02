from django.contrib import admin

from .models import StockItem, Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ["name", "address"]
    search_fields = ["name"]


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = [
        "product", "variant", "warehouse",
        "quantity", "reserved_quantity", "available_display",
        "low_stock_threshold", "is_low_stock_display",
    ]
    list_filter = ["warehouse", "low_stock_threshold"]
    search_fields = ["product__title", "variant__sku"]

    @admin.display(description="Available")
    def available_display(self, obj):
        return obj.available

    @admin.display(description="Low Stock?", boolean=True)
    def is_low_stock_display(self, obj):
        return obj.is_low_stock
