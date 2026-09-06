from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from orders.models import Order, OrderStatusHistory

from .gateways import PaymentGatewayError
from .models import Payment

User = get_user_model()


@override_settings(ZARINPAL_MERCHANT_ID="test-merchant-id", ZARINPAL_SANDBOX=True)
class InitiatePaymentTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="pay@test.com", password="TestPass123!"
        )
        self.order = Order.objects.create(
            user=self.user,
            order_number="TS-20260903-0099",
            total_amount=Decimal("5000000"),
            final_amount=Decimal("5000000"),
        )

    @patch("payments.gateways.requests.post")
    def test_initiate_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "Status": 100,
            "Authority": "test-authority-123",
        }
        mock_post.return_value.raise_for_status = lambda: None

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/payments/initiate/",
            {
                "order_id": self.order.id,
                "gateway": "zarinpal",
                "callback_url": "http://localhost:3000/payment/callback",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("payment_url", resp.data)
        self.assertIn("authority", resp.data)
        self.assertEqual(resp.data["authority"], "test-authority-123")

        # Verify payment record created
        payment = Payment.objects.get(id=resp.data["payment_id"])
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.gateway, "zarinpal")

    def test_initiate_order_not_found(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/payments/initiate/",
            {
                "order_id": 99999,
                "gateway": "zarinpal",
                "callback_url": "http://localhost:3000/callback",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_initiate_wrong_owner(self):
        other = User.objects.create_user(email="other@test.com", password="Pass123!")
        self.client.force_authenticate(user=other)
        resp = self.client.post(
            "/api/payments/initiate/",
            {
                "order_id": self.order.id,
                "gateway": "zarinpal",
                "callback_url": "http://localhost:3000/callback",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_initiate_already_paid_order(self):
        self.order.status = Order.Status.PAID
        self.order.save()
        Payment.objects.create(
            order=self.order,
            gateway="zarinpal",
            amount=self.order.final_amount,
            status=Payment.Status.SUCCESS,
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/payments/initiate/",
            {
                "order_id": self.order.id,
                "gateway": "zarinpal",
                "callback_url": "http://localhost:3000/callback",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("payments.gateways.requests.post")
    def test_initiate_gateway_failure(self, mock_post):
        mock_post.side_effect = PaymentGatewayError("Connection timeout")

        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/payments/initiate/",
            {
                "order_id": self.order.id,
                "gateway": "zarinpal",
                "callback_url": "http://localhost:3000/callback",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_502_BAD_GATEWAY)
        payment = Payment.objects.filter(order=self.order).first()
        self.assertEqual(payment.status, Payment.Status.FAILED)


@override_settings(ZARINPAL_MERCHANT_ID="test-merchant-id", ZARINPAL_SANDBOX=True)
class PaymentCallbackTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="callback@test.com", password="TestPass123!"
        )
        self.order = Order.objects.create(
            user=self.user,
            order_number="TS-20260903-0098",
            total_amount=Decimal("3000000"),
            final_amount=Decimal("3000000"),
        )
        self.payment = Payment.objects.create(
            order=self.order,
            gateway="zarinpal",
            amount=self.order.final_amount,
            status=Payment.Status.PENDING,
            transaction_ref="test-authority-456",
            gateway_data={"authority": "test-authority-456"},
        )

    @patch("payments.gateways.requests.post")
    def test_callback_success(self, mock_post):
        # Mock verify response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "Status": 100,
            "RefID": 123456789,
            "CardPan": "6274123412341234",
        }
        mock_post.return_value.raise_for_status = lambda: None

        resp = self.client.get(
            "/api/payments/callback/",
            {"authority": "test-authority-456", "Status": "OK"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "success")
        self.assertEqual(resp.data["transaction_ref"], 123456789)

        # Verify order status updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)

        # Verify status history
        history = OrderStatusHistory.objects.filter(
            order=self.order, status=Order.Status.PAID
        )
        self.assertEqual(history.count(), 1)

        # Verify payment updated
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.SUCCESS)
        self.assertIsNotNone(self.payment.paid_at)

    def test_callback_gateway_failure(self):
        resp = self.client.get(
            "/api/payments/callback/",
            {"authority": "test-authority-456", "Status": "NOK"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "failed")

        # Order should NOT be updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)

    def test_callback_invalid_authority(self):
        resp = self.client.get(
            "/api/payments/callback/",
            {"authority": "nonexistent", "Status": "OK"},
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    @patch("payments.gateways.requests.post")
    def test_callback_verify_failure(self, mock_post):
        mock_post.side_effect = PaymentGatewayError("Verify failed")

        resp = self.client.get(
            "/api/payments/callback/",
            {"authority": "test-authority-456", "Status": "OK"},
        )
        self.assertEqual(resp.status_code, status.HTTP_502_BAD_GATEWAY)
