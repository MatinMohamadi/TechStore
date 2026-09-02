from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Address

User = get_user_model()


class RegisterAPITest(TestCase):
    """Tests for POST /api/auth/register/"""

    def setUp(self):
        self.client = APIClient()
        self.valid_data = {
            "email": "test@example.com",
            "password": "TestPass123!",
            "password_confirm": "TestPass123!",
            "first_name": "Ali",
            "last_name": "Ahmadi",
        }

    def test_successful_registration(self):
        response = self.client.post("/api/auth/register/", self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])
        self.assertEqual(response.data["user"]["email"], "test@example.com")
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

    def test_duplicate_email_registration(self):
        User.objects.create_user(email="test@example.com", password="TestPass123!")
        response = self.client.post("/api/auth/register/", self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_mismatch(self):
        data = self.valid_data.copy()
        data["password_confirm"] = "WrongPass123!"
        response = self.client.post("/api/auth/register/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_fields(self):
        response = self.client.post("/api/auth/register/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginAPITest(TestCase):
    """Tests for POST /api/auth/login/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com", password="TestPass123!"
        )

    def test_successful_login(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "test@example.com", "password": "TestPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)
        self.assertEqual(response.data["user"]["email"], "test@example.com")

    def test_wrong_password(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "test@example.com", "password": "WrongPass"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_email(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "noone@example.com", "password": "TestPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AddressAPITest(TestCase):
    """Tests for /api/addresses/ CRUD"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com", password="TestPass123!"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com", password="OtherPass123!"
        )
        self.address_data = {
            "title": "Home",
            "province": "Tehran",
            "city": "Tehran",
            "postal_code": "1234567890",
            "full_address": "123 Main St",
            "receiver_name": "Ali Ahmadi",
            "receiver_phone": "09121234567",
        }
        self.client.force_authenticate(user=self.user)

    def test_create_address(self):
        response = self.client.post("/api/addresses/", self.address_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Home")

    def test_list_own_addresses_only(self):
        Address.objects.create(user=self.user, **self.address_data)
        Address.objects.create(
            user=self.other_user,
            title="Other Home",
            province="Isfahan",
            city="Isfahan",
            postal_code="0987654321",
            full_address="456 Other St",
            receiver_name="Sara",
            receiver_phone="09351234567",
        )
        response = self.client.get("/api/addresses/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_cannot_access_other_user_address(self):
        other_address = Address.objects.create(
            user=self.other_user,
            title="Other Home",
            province="Isfahan",
            city="Isfahan",
            postal_code="0987654321",
            full_address="456 Other St",
            receiver_name="Sara",
            receiver_phone="09351234567",
        )
        response = self.client.get(f"/api/addresses/{other_address.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_address(self):
        addr = Address.objects.create(user=self.user, **self.address_data)
        response = self.client.delete(f"/api/addresses/{addr.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Address.objects.filter(pk=addr.pk).exists())

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/addresses/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
