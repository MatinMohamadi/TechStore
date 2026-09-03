from django.db import models


class Payment(models.Model):
    """Payment transaction record."""

    class Gateway(models.TextChoices):
        ZARINPAL = "zarinpal", "Zarinpal"
        IDPAY = "idpay", "IDPay"
        STRIPE = "stripe", "Stripe"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    gateway = models.CharField(
        max_length=20, choices=Gateway.choices, default=Gateway.ZARINPAL
    )
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    transaction_ref = models.CharField(max_length=100, blank=True, null=True)
    gateway_data = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.id} - {self.gateway} - {self.status}"
