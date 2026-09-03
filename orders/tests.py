from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Address
from cart.models import Cart, CartItem
from catalog.models import Category, Product
from inventory.models import StockItem, Warehouse

from .models import Order, OrderItem, OrderStatusHistory

User = get_user_model()


class CheckoutTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="checkout@test.com", password="TestPass123!"
        )
        self.warehouse = Warehouse.objects.create(name="Main WH", address="Tehran")
        self.category = Category.objects.create(name="Components", slug="components")
        self.product = Product.objects.create(
            title="RTX 5080",
            category=self.category,
            base_price=45000000,
            sku="CHECKOUT-001",
            status="active",
        )
        StockItem.objects.create(
            product=self.product, warehouse=self.warehouse,
            quantity=10, reserved_quantity=0,
        )
        self.address = Address.objects.create(
            user=self.user,
            title="Home",
            province="Tehran",
            city="Tehran",
            postal_code="1234567890",
            full_address="123 Main St",
            receiver_name="Test User",
            receiver_phone="09121234567",
        )

    def _add_to_cart(self, quantity=2):
        """Helper: add product to user's cart and reserve stock."""
        cart, _ = Cart.objects.get_or_create(user=self.user)
        from inventory.services import reserve_stock
        reserve_stock(self.product, quantity)
        CartItem.objects.create(
            cart=cart, product=self.product,
            quantity=quantity,
            unit_price_snapshot=self.product.effective_price,
        )
        return cart

    def test_successful_checkout(self):
        self._add_to_cart(2)
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/orders/checkout/",
            {
                "shipping_address_id": self.address.id,
                "shipping_cost": 50000,
                "note": "Please ship quickly",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["total_amount"], "90000000")
        self.assertEqual(data["shipping_cost"], "50000")
        self.assertEqual(data["final_amount"], "90050000")
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["quantity"], 2)

        # Verify cart is deleted
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

        # Verify stock was reduced
        from inventory.services import get_available_stock
        available = get_available_stock(product=self.product)
        self.assertEqual(available, 8)

    def test_checkout_empty_cart(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/orders/checkout/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_creates_status_history(self):
        self._add_to_cart(1)
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/orders/checkout/",
            {"shipping_cost": 0},
            format="json",
        )
        order = Order.objects.get(pk=response.data["id"])
        history = order.status_history.all()
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().status, Order.Status.PENDING)


class OrderAccessTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email="owner@test.com", password="Pass123!"
        )
        self.other = User.objects.create_user(
            email="other@test.com", password="Pass123!"
        )
        self.order = Order.objects.create(
            user=self.owner,
            order_number="TS-20260902-0001",
        )

    def test_owner_can_see_order(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f"/api/orders/{self.order.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_see_order(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(f"/api/orders/{self.order.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_cannot_see_orders(self):
        response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_order_list_excludes_others(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get("/api/orders/")
        self.assertEqual(response.data["count"], 0)
