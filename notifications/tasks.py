"""
Async email notification tasks for TechStore.

Uses Celery with Redis as broker. In development, emails are printed
to the console (django.core.mail.backends.console.EmailBackend).
"""
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email(self, order_id):
    """Send order confirmation email after successful payment."""
    from orders.models import Order

    try:
        order = Order.objects.select_related("user").get(pk=order_id)
    except Order.DoesNotExist:
        return

    user = order.user
    subject = f"TechStore - Order #{order.order_number} Confirmed"

    # Render HTML email
    html_message = render_to_string(
        "emails/order_confirmation.html",
        {
            "user": user,
            "order": order,
        },
    )
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email="TechStore <noreply@techstore.com>",
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_order_status_change_email(self, order_id, old_status, new_status):
    """Send email when order status changes."""
    from orders.models import Order

    try:
        order = Order.objects.select_related("user").get(pk=order_id)
    except Order.DoesNotExist:
        return

    user = order.user
    status_labels = dict(Order.Status.choices)
    subject = f"TechStore - Order #{order.order_number} status updated"

    html_message = render_to_string(
        "emails/order_status_change.html",
        {
            "user": user,
            "order": order,
            "old_status": old_status,
            "new_status": new_status,
            "new_status_label": status_labels.get(new_status, new_status),
        },
    )
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email="TechStore <noreply@techstore.com>",
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
