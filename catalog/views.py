from django.db.models import Q
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from .models import Brand, Category, Product
from .serializers import (
    BrandDetailSerializer,
    BrandListSerializer,
    CategoryDetailSerializer,
    CategoryListSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """GET/POST /api/categories/ — List/create categories (tree structure)."""

    queryset = Category.objects.all()
    permission_classes = []  # AllowAny — read-only for customers
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return CategoryListSerializer
        return CategoryDetailSerializer


class BrandViewSet(viewsets.ModelViewSet):
    """GET/POST /api/brands/ — List/create brands."""

    queryset = Brand.objects.all()
    permission_classes = []
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return BrandListSerializer
        return BrandDetailSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    GET/POST /api/products/ — List/create products with filtering,
    search, and ordering.

    Query params:
      - category: category ID
      - brand: brand ID
      - min_price / max_price: price range
      - attr_<id>: attribute value filter (e.g. attr_1=16GB)
      - search: full-text search on title + description
      - ordering: price, -price, created_at, -created_at, title, -title
      - featured: true/false
      - status: draft/active/inactive
    """

    queryset = Product.objects.select_related("category", "brand").prefetch_related(
        "images", "attribute_values__attribute", "variants"
    )
    filter_backends = [SearchFilter]
    permission_classes = []
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action in ("list",):
            return ProductListSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        # Filter by category
        category = params.get("category")
        if category:
            qs = qs.filter(category_id=category)

        # Filter by brand
        brand = params.get("brand")
        if brand:
            qs = qs.filter(brand_id=brand)

        # Filter by price range
        min_price = params.get("min_price")
        if min_price:
            qs = qs.filter(base_price__gte=min_price)

        max_price = params.get("max_price")
        if max_price:
            qs = qs.filter(base_price__lte=max_price)

        # Filter by featured
        featured = params.get("featured")
        if featured is not None:
            qs = qs.filter(is_featured=featured.lower() == "true")

        # Filter by status
        status_param = params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        # Dynamic attribute filters: attr_<id>=<value>
        for key, value in params.items():
            if key.startswith("attr_"):
                attr_id = key.replace("attr_", "")
                qs = qs.filter(
                    attribute_values__attribute_id=attr_id,
                    attribute_values__value__icontains=value,
                )

        # Text search on title and description
        search = params.get("search")
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        return qs.distinct()

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        # Filter by category
        category = params.get("category")
        if category:
            qs = qs.filter(category_id=category)

        # Filter by brand
        brand = params.get("brand")
        if brand:
            qs = qs.filter(brand_id=brand)

        # Filter by price range
        min_price = params.get("min_price")
        if min_price:
            qs = qs.filter(base_price__gte=min_price)

        max_price = params.get("max_price")
        if max_price:
            qs = qs.filter(base_price__lte=max_price)

        # Filter by featured
        featured = params.get("featured")
        if featured is not None:
            qs = qs.filter(is_featured=featured.lower() == "true")

        # Filter by status
        status_param = params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        # Dynamic attribute filters: attr_<id>=<value>
        for key, value in params.items():
            if key.startswith("attr_"):
                attr_id = key.replace("attr_", "")
                qs = qs.filter(
                    attribute_values__attribute_id=attr_id,
                    attribute_values__value__icontains=value,
                )

        # Text search on title and description
        search = params.get("search")
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        # Ordering (map user-friendly names to actual field names)
        ordering = params.get("ordering")
        ordering_map = {
            "price": "base_price",
            "-price": "-base_price",
            "created_at": "created_at",
            "-created_at": "-created_at",
            "title": "title",
            "-title": "-title",
        }
        if ordering and ordering in ordering_map:
            qs = qs.order_by(ordering_map[ordering])

        return qs.distinct()
