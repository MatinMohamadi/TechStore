from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Review
from .serializers import ReviewSerializer


@extend_schema_view(
    get=extend_schema(
        summary="List approved reviews",
        description="Returns approved reviews for a specific product.",
        tags=["Reviews"],
    ),
    post=extend_schema(
        summary="Submit a product review",
        description=(
            "Submit a review for a product. Only users who have purchased "
            "the product can submit a review. Each user can review a product only once. "
            "Reviews require admin approval before appearing publicly."
        ),
        tags=["Reviews"],
    ),
)
class ProductReviewListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/products/{id}/reviews/ — List approved reviews for a product
    POST /api/products/{id}/reviews/ — Submit a review (buyer only)
    """

    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):

        product_id = self.kwargs.get("pk")
        return Review.objects.filter(
            product_id=product_id, is_approved=True
        ).select_related("user")

    def perform_create(self, serializer):
        from catalog.models import Product

        product = Product.objects.get(pk=self.kwargs["pk"])
        serializer.save(product=product)

    def create(self, request, *args, **kwargs):
        """Override to pass product context to serializer validation."""
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required to submit a review."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        from catalog.models import Product

        try:
            product = Product.objects.get(pk=self.kwargs["pk"])
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Pass product to validation context
        data = request.data.copy()
        data["product"] = product.id

        serializer = self.get_serializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
