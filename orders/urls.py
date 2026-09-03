from django.urls import path

from .views import CheckoutView, OrderDetailView, OrderListView

app_name = "orders"

urlpatterns = [
    path("orders/checkout/", CheckoutView.as_view(), name="checkout"),
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
]
