from django.urls import path

from .views import InitiatePaymentView, PaymentCallbackView

app_name = "payments"

urlpatterns = [
    path("payments/initiate/", InitiatePaymentView.as_view(), name="payment-initiate"),
    path("payments/callback/", PaymentCallbackView.as_view(), name="payment-callback"),
]
