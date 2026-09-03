from django.contrib.auth import authenticate, get_user_model
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Address
from .serializers import (
    AddressSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)

User = get_user_model()


@extend_schema_view(
    post=extend_schema(
        summary="Register a new user",
        description="Create a new account with email and password. Returns JWT tokens.",
        tags=["Auth"],
        examples=[
            OpenApiExample(
                "Registration",
                value={
                    "email": "user@example.com",
                    "password": "SecureP@ss123",
                    "password_confirm": "SecureP@ss123",
                    "first_name": "Ali",
                    "last_name": "Ahmadi",
                },
            )
        ],
    )
)
class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — Register a new user."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserProfileSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    post=extend_schema(
        summary="Login and get JWT tokens",
        description="Authenticate with email and password. Returns access and refresh tokens.",
        tags=["Auth"],
        examples=[
            OpenApiExample(
                "Login",
                value={
                    "email": "user@example.com",
                    "password": "SecureP@ss123",
                },
            )
        ],
    )
)
class LoginView(APIView):
    """POST /api/auth/login/ — Login with email and password."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        if user is None:
            return Response(
                {"error": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"error": "Account is disabled."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserProfileSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    get=extend_schema(
        summary="Get current user profile",
        description="Returns the authenticated user's profile information.",
        tags=["Auth"],
    ),
    put=extend_schema(
        summary="Update profile",
        description="Full update of the authenticated user's profile.",
        tags=["Auth"],
    ),
    patch=extend_schema(
        summary="Partial update profile",
        description="Partial update of the authenticated user's profile.",
        tags=["Auth"],
    ),
)
class ProfileView(generics.RetrieveUpdateAPIView):
    """GET/PUT/PATCH /api/auth/me/ — View or update profile."""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema_view(
    get=extend_schema(
        summary="List user addresses",
        description="Returns all addresses for the authenticated user.",
        tags=["Addresses"],
    ),
    post=extend_schema(
        summary="Create a new address",
        description="Add a new shipping address. Only one address can be default.",
        tags=["Addresses"],
    ),
)
class AddressListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/addresses/ — List or create addresses."""

    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


@extend_schema_view(
    get=extend_schema(
        summary="Get address detail",
        description="Returns a specific address by ID (owner only).",
        tags=["Addresses"],
    ),
    put=extend_schema(
        summary="Update address",
        description="Full update of a specific address.",
        tags=["Addresses"],
    ),
    patch=extend_schema(
        summary="Partial update address",
        description="Partial update of a specific address.",
        tags=["Addresses"],
    ),
    delete=extend_schema(
        summary="Delete address",
        description="Remove a specific address.",
        tags=["Addresses"],
    ),
)
class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/addresses/{id}/"""

    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
