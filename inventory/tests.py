import threading
import unittest

from django.db import connection
from django.test import TestCase, TransactionTestCase

from catalog.models import Category, Product

from .models import StockItem, Warehouse
from .services import (
    InsufficientStockError,
    confirm_stock_reduction,
    get_available_stock,
    release_stock,
    reserve_stock,
)


def is_sqlite():
    return connection.vendor == "sqlite"


class StockItemModelTest(TestCase):
    def setUp(self):
        self.warehouse = Warehouse.objects.create(name="Main WH", address="Tehran")
        self.category = Category.objects.create(name="Components", slug="components")
        self.product = Product.objects.create(
            title="Test Product",
            category=self.category,
            base_price=1000000,
            sku="TEST-001",
            status="active",
        )

    def test_available_stock(self):
        StockItem.objects.create(
            product=self.product, warehouse=self.warehouse,
            quantity=10, reserved_quantity=3,
        )
        item = StockItem.objects.first()
        self.assertEqual(item.available, 7)

    def test_in_stock(self):
        item = StockItem.objects.create(
            product=self.product, warehouse=self.warehouse,
            quantity=5, reserved_quantity=5,
        )
        self.assertFalse(item.is_in_stock)

    def test_low_stock(self):
        item = StockItem.objects.create(
            product=self.product, warehouse=self.warehouse,
            quantity=10, reserved_quantity=8, low_stock_threshold=3,
        )
        self.assertTrue(item.is_low_stock)  # available=2 <= threshold=3


class StockServiceTest(TestCase):
    def setUp(self):
        self.warehouse = Warehouse.objects.create(name="Main WH", address="Tehran")
        self.category = Category.objects.create(name="Components", slug="components")
        self.product = Product.objects.create(
            title="Test Product",
            category=self.category,
            base_price=1000000,
            sku="TEST-001",
            status="active",
        )
        StockItem.objects.create(
            product=self.product, warehouse=self.warehouse,
            quantity=10, reserved_quantity=0,
        )

    def test_get_available_stock(self):
        available = get_available_stock(product=self.product)
        self.assertEqual(available, 10)

    def test_reserve_stock_success(self):
        result = reserve_stock(self.product, 3)
        self.assertTrue(result)
        item = StockItem.objects.get(product=self.product)
        self.assertEqual(item.reserved_quantity, 3)
        self.assertEqual(item.available, 7)

    def test_reserve_stock_insufficient(self):
        with self.assertRaises(InsufficientStockError) as ctx:
            reserve_stock(self.product, 15)
        self.assertEqual(ctx.exception.available, 10)
        self.assertEqual(ctx.exception.requested, 15)

    def test_reserve_then_release(self):
        reserve_stock(self.product, 5)
        release_stock(self.product, 5)
        item = StockItem.objects.get(product=self.product)
        self.assertEqual(item.reserved_quantity, 0)
        self.assertEqual(item.available, 10)

    def test_confirm_stock_reduction(self):
        reserve_stock(self.product, 4)
        confirm_stock_reduction(self.product, 4)
        item = StockItem.objects.get(product=self.product)
        self.assertEqual(item.quantity, 6)
        self.assertEqual(item.reserved_quantity, 0)
        self.assertEqual(item.available, 6)

    def test_reserve_zero_raises(self):
        with self.assertRaises(ValueError):
            reserve_stock(self.product, 0)

    def test_reserve_negative_raises(self):
        with self.assertRaises(ValueError):
            reserve_stock(self.product, -1)

    def test_multiple_reservations(self):
        reserve_stock(self.product, 3)
        reserve_stock(self.product, 2)
        item = StockItem.objects.get(product=self.product)
        self.assertEqual(item.reserved_quantity, 5)
        self.assertEqual(item.available, 5)

    def test_reserve_exactly_available(self):
        reserve_stock(self.product, 10)
        item = StockItem.objects.get(product=self.product)
        self.assertEqual(item.reserved_quantity, 10)
        self.assertEqual(item.available, 0)
        # Now no more available
        with self.assertRaises(InsufficientStockError):
            reserve_stock(self.product, 1)


class StockConcurrencyTest(TransactionTestCase):
    """
    Test concurrent stock reservations to verify atomicity.

    NOTE: SQLite uses database-level locks (not row-level), so true
    concurrency testing requires PostgreSQL.  On SQLite, these tests
    verify the logic correctness via sequential simulation.
    """

    def setUp(self):
        self.warehouse = Warehouse.objects.create(name="Main WH", address="Tehran")
        self.category = Category.objects.create(name="Components", slug="components")
        self.product = Product.objects.create(
            title="Limited Product",
            category=self.category,
            base_price=5000000,
            sku="LIMITED-001",
            status="active",
        )
        StockItem.objects.create(
            product=self.product, warehouse=self.warehouse,
            quantity=5, reserved_quantity=0,
        )

    @unittest.skipIf(is_sqlite(), "SQLite does not support row-level select_for_update")
    def test_concurrent_reserve_last_units(self):
        """Two threads try to reserve 3 each from 5 available. One should fail."""
        results = []

        def try_reserve(qty):
            try:
                reserve_stock(self.product, qty)
                results.append(("ok", qty))
            except InsufficientStockError:
                results.append(("fail", qty))

        t1 = threading.Thread(target=try_reserve, args=(3,))
        t2 = threading.Thread(target=try_reserve, args=(3,))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        successes = [r for r in results if r[0] == "ok"]
        failures = [r for r in results if r[0] == "fail"]

        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)

        item = StockItem.objects.get(product=self.product)
        self.assertEqual(item.quantity, 5)
        self.assertEqual(item.reserved_quantity, 3)
        self.assertEqual(item.available, 2)

    @unittest.skipIf(is_sqlite(), "SQLite does not support row-level select_for_update")
    def test_concurrent_reserve_exact_stock(self):
        """Two threads try to reserve 3 each from exactly 6 available. Both should succeed."""
        StockItem.objects.filter(product=self.product).update(quantity=6)

        results = []

        def try_reserve(qty):
            try:
                reserve_stock(self.product, qty)
                results.append(("ok", qty))
            except InsufficientStockError:
                results.append(("fail", qty))

        t1 = threading.Thread(target=try_reserve, args=(3,))
        t2 = threading.Thread(target=try_reserve, args=(3,))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        successes = [r for r in results if r[0] == "ok"]
        failures = [r for r in results if r[0] == "fail"]

        self.assertEqual(len(successes), 2)
        self.assertEqual(len(failures), 0)

        item = StockItem.objects.get(product=self.product)
        self.assertEqual(item.quantity, 6)
        self.assertEqual(item.reserved_quantity, 6)
        self.assertEqual(item.available, 0)

    def test_concurrent_logic_sequential(self):
        """
        Verify correctness of reserve/release/confirm logic sequentially.
        Simulates the full lifecycle: reserve -> confirm -> check stock.
        """
        # Start: quantity=5, reserved=0, available=5
        self.assertEqual(get_available_stock(product=self.product), 5)

        # Reserve 3
        reserve_stock(self.product, 3)
        item = StockItem.objects.get(product=self.product)
        self.assertEqual(item.quantity, 5)
        self.assertEqual(item.reserved_quantity, 3)
        self.assertEqual(get_available_stock(product=self.product), 2)

        # Try to reserve 3 more — should fail (only 2 available)
        with self.assertRaises(InsufficientStockError):
            reserve_stock(self.product, 3)

        # Reserve remaining 2
        reserve_stock(self.product, 2)
        self.assertEqual(get_available_stock(product=self.product), 0)

        # Confirm 4 (simulating successful payment)
        confirm_stock_reduction(self.product, 4)
        item = StockItem.objects.get(product=self.product)
        self.assertEqual(item.quantity, 1)  # 5 - 4 = 1
        self.assertEqual(item.reserved_quantity, 1)  # 5 - 4 = 1
        self.assertEqual(get_available_stock(product=self.product), 0)

        # Release remaining 1 (simulating cart expiry)
        release_stock(self.product, 1)
        item = StockItem.objects.get(product=self.product)
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.reserved_quantity, 0)
        self.assertEqual(get_available_stock(product=self.product), 1)
