from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AddressDetailView,
    AddressListCreateView,
    LoginView,
    ProfileView,
    RegisterView,
)

app_name = "accounts"

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/me/", ProfileView.as_view(), name="profile"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("addresses/", AddressListCreateView.as_view(), name="address-list"),
    path("addresses/<int:pk>/", AddressDetailView.as_view(), name="address-detail"),
]
