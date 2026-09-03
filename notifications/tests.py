from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings

from orders.models import Order, OrderStatusHistory

from .tasks import send_order_confirmation_email, send_order_status_change_email

User = get_user_model()


class CeleryTaskTest(TestCase):
    """Test that Celery tasks execute correctly in eager mode."""

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_order_confirmation_email_sent(self):
        user = User.objects.create_user(
            email="celery@test.com", password="TestPass123!"
        )
        order = Order.objects.create(
            user=user,
            order_number="TS-20260903-CEL01",
            total_amount=5000000,
            final_amount=5000000,
            status=Order.Status.PAID,
        )

        result = send_order_confirmation_email.delay(order.id)
        self.assertTrue(result.successful())

        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn("Confirmed", sent.subject)
        self.assertIn("celery@test.com", sent.to)
        self.assertIn(order.order_number, sent.body)

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_order_status_change_email_sent(self):
        user = User.objects.create_user(
            email="celery@test.com", password="TestPass123!"
        )
        order = Order.objects.create(
            user=user,
            order_number="TS-20260903-CEL02",
            total_amount=3000000,
            final_amount=3000000,
            status=Order.Status.PAID,
        )

        result = send_order_status_change_email.delay(
            order.id, "paid", "shipped"
        )
        self.assertTrue(result.successful())

        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn("status updated", sent.subject)
        self.assertIn(order.order_number, sent.body)

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_order_update_status_sends_email(self):
        """Test Order.update_status() triggers email notification."""
        user = User.objects.create_user(
            email="celery@test.com", password="TestPass123!"
        )
        order = Order.objects.create(
            user=user,
            order_number="TS-20260903-CEL03",
            total_amount=2000000,
            final_amount=2000000,
            status=Order.Status.PAID,
        )

        order.update_status(Order.Status.SHIPPED, note="Shipped via Post")

        order.refresh_from_db()
        self.assertEqual(order.status, "shipped")
        self.assertEqual(
            order.status_history.filter(status="shipped").count(), 1
        )
        # Email was sent
        self.assertEqual(len(mail.outbox), 1)
