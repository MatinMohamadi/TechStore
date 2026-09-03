from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from cart.models import Cart, CartItem
from catalog.models import Category, Product
from inventory.models import StockItem, Warehouse
from inventory.services import reserve_stock

from .models import Coupon

User = get_user_model()


class CouponValidationTest(TestCase):
    """Test Coupon model validation logic."""

    def setUp(self):
        self.coupon = Coupon.objects.create(
            code="TEST10",
            discount_type=Coupon.DiscountType.PERCENT,
            value=10,
            min_order_amount=100000,
            max_uses=5,
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=30),
            is_active=True,
        )

    def test_valid_coupon(self):
        discount = self.coupon.calculate_discount(1000000)
        self.assertEqual(discount, 100000)  # 10% of 1,000,000

    def test_fixed_coupon(self):
        self.coupon.discount_type = Coupon.DiscountType.FIXED
        self.coupon.value = 50000
        self.coupon.save()
        discount = self.coupon.calculate_discount(200000)
        self.assertEqual(discount, 50000)

    def test_expired_coupon(self):
        self.coupon.valid_to = timezone.now() - timedelta(days=1)
        self.coupon.save()
        with self.assertRaises(ValueError) as ctx:
            self.coupon.calculate_discount(1000000)
        self.assertIn("expired", str(ctx.exception))

    def test_not_yet_active(self):
        self.coupon.valid_from = timezone.now() + timedelta(days=1)
        self.coupon.save()
        with self.assertRaises(ValueError):
            self.coupon.calculate_discount(1000000)

    def test_min_order_not_met(self):
        with self.assertRaises(ValueError) as ctx:
            self.coupon.calculate_discount(50000)  # below 100,000
        self.assertIn("Minimum order", str(ctx.exception))

    def test_max_uses_exhausted(self):
        self.coupon.used_count = 5
        self.coupon.save()
        with self.assertRaises(ValueError) as ctx:
            self.coupon.calculate_discount(1000000)
        self.assertIn("usage limit", str(ctx.exception))

    def test_unlimited_coupon(self):
        self.coupon.max_uses = 0  # unlimited
        self.coupon.used_count = 999
        self.coupon.save()
        discount = self.coupon.calculate_discount(1000000)
        self.assertEqual(discount, 100000)

    def test_discount_cannot_exceed_order(self):
        self.coupon.discount_type = Coupon.DiscountType.FIXED
        self.coupon.value = 500000
        self.coupon.save()
        discount = self.coupon.calculate_discount(200000)
        self.assertEqual(discount, 200000)  # capped at order amount

    def test_inactive_coupon(self):
        self.coupon.is_active = False
        self.coupon.save()
        with self.assertRaises(ValueError):
            self.coupon.calculate_discount(1000000)


class ApplyCouponAPITest(TestCase):
    """Test POST /api/cart/apply-coupon/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="coupon@test.com", password="TestPass123!"
        )
        self.warehouse = Warehouse.objects.create(name="Main WH", address="Tehran")
        self.category = Category.objects.create(name="Peripherals", slug="peripherals")
        self.product = Product.objects.create(
            title="Gaming Mouse",
            category=self.category,
            base_price=2500000,
            sku="COUPON-001",
            status="active",
        )
        StockItem.objects.create(
            product=self.product, warehouse=self.warehouse,
            quantity=10, reserved_quantity=0,
        )
        self.coupon = Coupon.objects.create(
            code="SAVE20",
            discount_type=Coupon.DiscountType.PERCENT,
            value=20,
            min_order_amount=100000,
            max_uses=10,
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=30),
            is_active=True,
        )
        # Add item to cart
        self.client.force_authenticate(user=self.user)
        reserve_stock(self.product, 2)
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=2,
            unit_price_snapshot=self.product.effective_price,
        )

    def test_apply_valid_coupon(self):
        response = self.client.post(
            "/api/cart/apply-coupon/",
            {"code": "SAVE20"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["discount_type"], "percent")
        self.assertEqual(response.data["discount_amount"], "1000000")

    def test_apply_invalid_coupon(self):
        response = self.client.post(
            "/api/cart/apply-coupon/",
            {"code": "DOESNOTEXIST"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_apply_expired_coupon(self):
        self.coupon.valid_to = timezone.now() - timedelta(days=1)
        self.coupon.save()
        response = self.client.post(
            "/api/cart/apply-coupon/",
            {"code": "SAVE20"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_apply_coupon_below_min_amount(self):
        cheap_coupon = Coupon.objects.create(
            code="MIN500",
            discount_type=Coupon.DiscountType.PERCENT,
            value=10,
            min_order_amount=5000001,  # cart total is 5,000,000
            max_uses=10,
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=30),
            is_active=True,
        )
        response = self.client.post(
            "/api/cart/apply-coupon/",
            {"code": "MIN500"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_apply_to_empty_cart(self):
        # Clear the cart
        CartItem.objects.all().delete()
        response = self.client.post(
            "/api/cart/apply-coupon/",
            {"code": "SAVE20"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
