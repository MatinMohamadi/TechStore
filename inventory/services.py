"""
Inventory service — atomic stock operations.

All public functions use select_for_update + F() expressions to prevent
race conditions and overselling.  Call them inside a transaction.

NOTE: select_for_update provides true row-level locking on PostgreSQL.
On SQLite, it uses database-level locking which may raise OperationalError
under heavy concurrency.  The retry logic below handles this gracefully.
"""

import time

from django.db import OperationalError, transaction
from django.db.models import F, Sum

from .models import StockItem


class InsufficientStockError(Exception):
    """Raised when requested quantity exceeds available stock."""

    def __init__(self, available, requested, product_name=""):
        self.available = available
        self.requested = requested
        self.product_name = product_name
        super().__init__(
            f"Insufficient stock for '{product_name}': "
            f"available={available}, requested={requested}"
        )


def get_available_stock(product=None, variant=None):
    """Return total available stock across all warehouses."""
    qs = StockItem.objects.all()
    if product:
        qs = qs.filter(product=product)
    if variant:
        qs = qs.filter(variant=variant)

    result = qs.aggregate(
        total_quantity=Sum("quantity"),
        total_reserved=Sum("reserved_quantity"),
    )
    total_qty = result["total_quantity"] or 0
    total_res = result["total_reserved"] or 0
    return total_qty - total_res


def reserve_stock(product, quantity, variant=None, retries=3):
    """
    Atomically reserve `quantity` units for a cart/order.

    Uses select_for_update to lock rows and prevent concurrent overselling.
    On SQLite, retries on database lock errors.

    Raises:
        InsufficientStockError: if not enough available stock.
        ValueError: if quantity <= 0.
    """
    if quantity <= 0:
        raise ValueError("Quantity must be positive")

    for attempt in range(retries):
        try:
            with transaction.atomic():
                # Lock all stock items for this product/variant
                if variant:
                    qs = StockItem.objects.select_for_update().filter(variant=variant)
                else:
                    qs = StockItem.objects.select_for_update().filter(product=product)

                # Calculate total available
                total_available = 0
                for item in qs:
                    total_available += item.quantity - item.reserved_quantity

                if total_available < quantity:
                    raise InsufficientStockError(
                        available=total_available,
                        requested=quantity,
                        product_name=str(product),
                    )

                # Reserve across warehouses (FIFO: fill from each warehouse)
                remaining = quantity
                for item in qs:
                    item_avail = item.quantity - item.reserved_quantity
                    if item_avail <= 0:
                        continue
                    to_reserve = min(item_avail, remaining)
                    StockItem.objects.filter(pk=item.pk).update(
                        reserved_quantity=F("reserved_quantity") + to_reserve
                    )
                    remaining -= to_reserve
                    if remaining <= 0:
                        break

                return True
        except OperationalError:
            if attempt < retries - 1:
                time.sleep(0.01 * (attempt + 1))
                continue
            raise


def release_stock(product, quantity, variant=None, retries=3):
    """
    Release previously reserved stock (e.g. cart expired, order cancelled).

    Atomically decrements reserved_quantity across warehouses.
    """
    if quantity <= 0:
        raise ValueError("Quantity must be positive")

    for attempt in range(retries):
        try:
            with transaction.atomic():
                if variant:
                    qs = StockItem.objects.select_for_update().filter(variant=variant)
                else:
                    qs = StockItem.objects.select_for_update().filter(product=product)

                remaining = quantity
                for item in qs:
                    if item.reserved_quantity <= 0:
                        continue
                    to_release = min(item.reserved_quantity, remaining)
                    StockItem.objects.filter(pk=item.pk).update(
                        reserved_quantity=F("reserved_quantity") - to_release
                    )
                    remaining -= to_release
                    if remaining <= 0:
                        break

                return True
        except OperationalError:
            if attempt < retries - 1:
                time.sleep(0.01 * (attempt + 1))
                continue
            raise


def confirm_stock_reduction(product, quantity, variant=None, retries=3):
    """
    Permanently reduce stock after successful payment/order confirmation.

    Decrements both quantity AND reserved_quantity atomically.
    """
    if quantity <= 0:
        raise ValueError("Quantity must be positive")

    for attempt in range(retries):
        try:
            with transaction.atomic():
                if variant:
                    qs = StockItem.objects.select_for_update().filter(variant=variant)
                else:
                    qs = StockItem.objects.select_for_update().filter(product=product)

                remaining = quantity
                for item in qs:
                    if item.reserved_quantity <= 0:
                        continue
                    to_confirm = min(item.reserved_quantity, remaining)
                    StockItem.objects.filter(pk=item.pk).update(
                        quantity=F("quantity") - to_confirm,
                        reserved_quantity=F("reserved_quantity") - to_confirm,
                    )
                    remaining -= to_confirm
                    if remaining <= 0:
                        break

                return True
        except OperationalError:
            if attempt < retries - 1:
                time.sleep(0.01 * (attempt + 1))
                continue
            raise
