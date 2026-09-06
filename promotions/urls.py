from django.urls import path

from .views import ApplyCouponView

app_name = "promotions"

urlpatterns = [
    path("cart/apply-coupon/", ApplyCouponView.as_view(), name="apply-coupon"),
]
