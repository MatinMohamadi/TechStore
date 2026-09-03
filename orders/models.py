from django.conf import settings
from django.db import models


class Order(models.Model):
    """Customer order created from a cart."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELED = "canceled", "Canceled"
        REFUNDED = "refunded", "Refunded"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.PENDING
    )
    shipping_address = models.ForeignKey(
        "accounts.Address",
        on_delete=models.PROTECT,
        related_name="orders",
        null=True,
        blank=True,
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    final_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_number}"

    def recalculate_totals(self):
        """Recalculate order totals from items."""
        items_total = sum(item.total_price for item in self.items.all())
        self.total_amount = items_total
        self.final_amount = self.total_amount - self.discount_amount + self.shipping_cost
        self.save(update_fields=["total_amount", "final_amount"])

    @staticmethod
    def generate_order_number():
        """Generate unique order number: TS-YYYYMMDD-XXXX"""
        import datetime
        from django.utils import timezone

        today = timezone.now()
        prefix = f"TS-{today.strftime('%Y%m%d')}-"

        # Count orders created today
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        count = Order.objects.filter(created_at__gte=start_of_day).count()
        sequence = count + 1

        return f"{prefix}{sequence:04d}"


class OrderItem(models.Model):
    """A line item in an order."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT, related_name="order_items"
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=0)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity}x {self.product.title}"

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """Tracks every status change on an order."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="status_history"
    )
    status = models.CharField(max_length=12, choices=Order.Status.choices)
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status Histories"
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.order.order_number} -> {self.status}"
