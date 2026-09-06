from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import Category, Product
from orders.models import Order, OrderItem, OrderStatusHistory

from .models import Review

User = get_user_model()


class ReviewPermissionTest(TestCase):
    """Tests for review access rules."""

    def setUp(self):
        self.client = APIClient()
        self.buyer = User.objects.create_user(
            email="buyer@test.com", password="TestPass123!"
        )
        self.non_buyer = User.objects.create_user(
            email="nonbuyer@test.com", password="TestPass123!"
        )
        self.category = Category.objects.create(name="Peripherals", slug="peripherals")
        self.product = Product.objects.create(
            title="Gaming Mouse",
            category=self.category,
            base_price=2500000,
            sku="REVIEW-001",
            status="active",
        )

        # Create a paid order for buyer with this product
        self.order = Order.objects.create(
            user=self.buyer,
            order_number="TS-20260903-0100",
            total_amount=Decimal("2500000"),
            final_amount=Decimal("2500000"),
            status=Order.Status.PAID,
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=Decimal("2500000"),
        )
        OrderStatusHistory.objects.create(order=self.order, status=Order.Status.PAID)

    def test_buyer_can_review(self):
        self.client.force_authenticate(user=self.buyer)
        resp = self.client.post(
            f"/api/products/{self.product.id}/reviews/",
            {"rating": 5, "comment": "Great product!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["rating"], 5)
        self.assertFalse(resp.data["is_approved"])  # needs admin approval

    def test_non_buyer_cannot_review(self):
        self.client.force_authenticate(user=self.non_buyer)
        resp = self.client.post(
            f"/api/products/{self.product.id}/reviews/",
            {"rating": 4, "comment": "Nice"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_review_rejected(self):
        self.client.force_authenticate(user=self.buyer)
        # First review
        self.client.post(
            f"/api/products/{self.product.id}/reviews/",
            {"rating": 5, "comment": "Great!"},
            format="json",
        )
        # Second review — should fail
        resp = self.client.post(
            f"/api/products/{self.product.id}/reviews/",
            {"rating": 4, "comment": "Still good"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_approved_reviews_visible(self):
        self.client.force_authenticate(user=self.buyer)
        # Create review (not approved)
        self.client.post(
            f"/api/products/{self.product.id}/reviews/",
            {"rating": 5, "comment": "Hidden review"},
            format="json",
        )
        # List reviews (public)
        self.client.force_authenticate(user=None)
        resp = self.client.get(f"/api/products/{self.product.id}/reviews/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)  # not approved yet

        # Approve
        Review.objects.update(is_approved=True)
        resp = self.client.get(f"/api/products/{self.product.id}/reviews/")
        self.assertEqual(resp.data["count"], 1)

    def test_unauthenticated_can_read_approved_reviews(self):
        Review.objects.create(
            product=self.product,
            user=self.buyer,
            rating=5,
            comment="Good",
            is_approved=True,
        )
        resp = self.client.get(f"/api/products/{self.product.id}/reviews/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_unauthenticated_cannot_post_review(self):
        resp = self.client.post(
            f"/api/products/{self.product.id}/reviews/",
            {"rating": 5, "comment": "Test"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delivered_order_allows_review(self):
        """Users with delivered orders can also review."""
        self.order.status = Order.Status.DELIVERED
        self.order.save()
        self.client.force_authenticate(user=self.buyer)
        resp = self.client.post(
            f"/api/products/{self.product.id}/reviews/",
            {"rating": 4, "comment": "Delivered and happy"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
