from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id", "order", "gateway", "amount", "status",
        "transaction_ref", "paid_at", "created_at",
    ]
    list_filter = ["gateway", "status"]
    search_fields = ["order__order_number", "transaction_ref"]
    readonly_fields = [
        "order", "gateway", "amount", "transaction_ref",
        "gateway_data", "paid_at", "created_at",
    ]
