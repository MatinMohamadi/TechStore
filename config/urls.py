"""
URL configuration for TechStore project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

# Health check view
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({"status": "healthy", "service": "techstore"})


urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),
    # Health Check
    path("api/health/", health_check, name="health-check"),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # App URLs
    path("api/", include("accounts.urls")),
    path("api/", include("catalog.urls")),
    path("api/", include("cart.urls")),
    path("api/", include("orders.urls")),
    path("api/", include("payments.urls")),
    path("api/", include("promotions.urls")),
    path("api/", include("reviews.urls")),
    path("api/", include("support.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
