from django.contrib import admin

from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        "code", "discount_type", "value", "min_order_amount",
        "max_uses", "used_count", "valid_from", "valid_to", "is_active",
    ]
    list_filter = ["is_active", "discount_type"]
    search_fields = ["code"]
    readonly_fields = ["used_count"]
