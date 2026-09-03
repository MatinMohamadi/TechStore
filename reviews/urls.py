from django.urls import path

from .views import ProductReviewListCreateView

app_name = "reviews"

urlpatterns = [
    path(
        "products/<int:pk>/reviews/",
        ProductReviewListCreateView.as_view(),
        name="product-reviews",
    ),
]
