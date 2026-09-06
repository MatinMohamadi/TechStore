from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import Category, Product
from inventory.models import StockItem, Warehouse

from .models import Cart, CartItem

User = get_user_model()


class CartGuestTest(TestCase):
    """Test guest cart functionality."""

    def setUp(self):
        self.client = APIClient()
        self.warehouse = Warehouse.objects.create(name="Main WH", address="Tehran")
        self.category = Category.objects.create(name="Peripherals", slug="peripherals")
        self.product = Product.objects.create(
            title="Gaming Mouse",
            category=self.category,
            base_price=2500000,
            sku="MOUSE-001",
            status="active",
        )
        StockItem.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=10,
            reserved_quantity=0,
        )
        # Simulate guest session
        self.client.session.create()
        self.session_key = self.client.session.session_key

    def test_add_item_to_guest_cart(self):
        response = self.client.post(
            "/api/cart/items/",
            {"product_id": self.product.id, "quantity": 2},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["quantity"], 2)
        self.assertEqual(response.data["unit_price_snapshot"], "2500000")

    def test_guest_cart_view(self):
        self.client.post(
            "/api/cart/items/",
            {"product_id": self.product.id, "quantity": 1},
            format="json",
        )
        response = self.client.get("/api/cart/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["total_items"], 1)

    def test_exceeding_stock(self):
        response = self.client.post(
            "/api/cart/items/",
            {"product_id": self.product.id, "quantity": 15},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_update_quantity(self):
        resp = self.client.post(
            "/api/cart/items/",
            {"product_id": self.product.id, "quantity": 1},
            format="json",
        )
        item_id = resp.data["id"]
        response = self.client.patch(
            f"/api/cart/items/{item_id}/",
            {"quantity": 3},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], 3)

    def test_delete_item(self):
        resp = self.client.post(
            "/api/cart/items/",
            {"product_id": self.product.id, "quantity": 1},
            format="json",
        )
        item_id = resp.data["id"]
        response = self.client.delete(f"/api/cart/items/{item_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify cart is empty
        response = self.client.get("/api/cart/")
        self.assertEqual(len(response.data["items"]), 0)


class CartMergeTest(TestCase):
    """Test cart merge when guest logs in."""

    def setUp(self):
        self.client = APIClient()
        self.warehouse = Warehouse.objects.create(name="Main WH", address="Tehran")
        self.category = Category.objects.create(name="Peripherals", slug="peripherals")
        self.product1 = Product.objects.create(
            title="Mouse",
            category=self.category,
            base_price=2500000,
            sku="MOUSE-001",
            status="active",
        )
        self.product2 = Product.objects.create(
            title="Keyboard",
            category=self.category,
            base_price=3500000,
            sku="KB-001",
            status="active",
        )
        StockItem.objects.create(
            product=self.product1,
            warehouse=self.warehouse,
            quantity=10,
            reserved_quantity=0,
        )
        StockItem.objects.create(
            product=self.product2,
            warehouse=self.warehouse,
            quantity=5,
            reserved_quantity=0,
        )
        self.user = User.objects.create_user(
            email="merge@test.com", password="TestPass123!"
        )

    def test_merge_guest_cart_to_user(self):
        # 1. Guest adds items
        self.client.session.create()
        session_key = self.client.session.session_key

        self.client.post(
            "/api/cart/items/",
            {"product_id": self.product1.id, "quantity": 2},
            format="json",
        )
        self.client.post(
            "/api/cart/items/",
            {"product_id": self.product2.id, "quantity": 1},
            format="json",
        )

        # Verify guest cart has 2 items
        response = self.client.get("/api/cart/")
        self.assertEqual(len(response.data["items"]), 2)

        # 2. User logs in
        self.client.force_authenticate(user=self.user)

        # 3. Merge guest cart
        response = self.client.post(
            "/api/cart/merge/",
            {"session_key": session_key},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 2)

        # 4. Verify guest cart is deleted
        self.assertFalse(Cart.objects.filter(session_key=session_key).exists())

        # 5. Verify user cart has the items
        response = self.client.get("/api/cart/")
        self.assertEqual(len(response.data["items"]), 2)

    def test_merge_with_existing_user_cart(self):
        # User already has a cart with product1
        user_cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=user_cart,
            product=self.product1,
            quantity=1,
            unit_price_snapshot=self.product1.effective_price,
        )

        # Guest has product1 + product2
        self.client.session.create()
        session_key = self.client.session.session_key

        self.client.post(
            "/api/cart/items/",
            {"product_id": self.product1.id, "quantity": 2},
            format="json",
        )
        self.client.post(
            "/api/cart/items/",
            {"product_id": self.product2.id, "quantity": 1},
            format="json",
        )

        # Merge
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/cart/merge/",
            {"session_key": session_key},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # product1 should be merged (1+2=3), product2 should be added
        items = response.data["items"]
        self.assertEqual(len(items), 2)

        mouse_item = next(i for i in items if i["product"] == self.product1.id)
        kb_item = next(i for i in items if i["product"] == self.product2.id)
        self.assertEqual(mouse_item["quantity"], 3)
        self.assertEqual(kb_item["quantity"], 1)
