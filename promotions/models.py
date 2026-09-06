from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    """Discount coupon / campaign code."""

    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Percent"
        FIXED = "fixed", "Fixed Amount"

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(
        max_length=10, choices=DiscountType.choices, default=DiscountType.PERCENT
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        help_text="Percent (e.g. 10 for 10%) or fixed amount in IRR",
    )
    min_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        help_text="Minimum order amount required to use this coupon",
    )
    max_uses = models.PositiveIntegerField(
        default=0,
        help_text="0 = unlimited uses",
    )
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        ordering = ["-valid_from"]

    def __str__(self):
        return f"{self.code} ({self.discount_type}: {self.value})"

    @property
    def is_valid_now(self):
        """Check if coupon is currently valid (active + date range)."""
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_to

    @property
    def is_usage_exhausted(self):
        """Check if max uses reached (0 = unlimited)."""
        if self.max_uses == 0:
            return False
        return self.used_count >= self.max_uses

    def calculate_discount(self, order_amount):
        """
        Calculate discount amount for a given order total.

        Returns:
            discount_amount (Decimal): calculated discount
        Raises:
            ValueError: if coupon is invalid
        """
        if not self.is_valid_now:
            raise ValueError("Coupon is expired or not yet active.")
        if self.is_usage_exhausted:
            raise ValueError("Coupon usage limit reached.")
        if order_amount < self.min_order_amount:
            raise ValueError(
                f"Minimum order amount is {self.min_order_amount} IRR. "
                f"Your order is {order_amount} IRR."
            )

        if self.discount_type == self.DiscountType.PERCENT:
            discount = order_amount * self.value / 100
        else:
            discount = self.value

        # Discount cannot exceed order amount
        return min(discount, order_amount)

    def increment_usage(self):
        """Increment used_count by 1."""
        Coupon.objects.filter(pk=self.pk).update(used_count=models.F("used_count") + 1)
