from django.db import models


class Warehouse(models.Model):
    """Physical warehouse / storage location."""

    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)

    class Meta:
        verbose_name = "Warehouse"
        verbose_name_plural = "Warehouses"

    def __str__(self):
        return self.name


class StockItem(models.Model):
    """
    Stock record linking a product (or variant) to a warehouse.

    - quantity: total units in warehouse
    - reserved_quantity: units reserved by pending carts/orders
    - available = quantity - reserved_quantity  (computed)
    """

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="stock_items",
        null=True,
        blank=True,
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="stock_items",
        null=True,
        blank=True,
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="stock_items",
    )
    quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)

    class Meta:
        verbose_name = "Stock Item"
        verbose_name_plural = "Stock Items"
        constraints = [
            models.CheckConstraint(
                check=models.Q(reserved_quantity__lte=models.F("quantity")),
                name="reserved_lte_quantity",
            )
        ]

    def __str__(self):
        target = self.product or self.variant
        return f"{target} @ {self.warehouse}"

    @property
    def available(self):
        """Units available for new reservations."""
        return self.quantity - self.reserved_quantity

    @property
    def is_low_stock(self):
        return self.available <= self.low_stock_threshold

    @property
    def is_in_stock(self):
        return self.available > 0
