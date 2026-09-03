from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Ticket, TicketMessage
from .serializers import (
    CreateTicketSerializer,
    TicketDetailSerializer,
    TicketListSerializer,
    TicketMessageCreateSerializer,
    TicketMessageSerializer,
    TicketStatusSerializer,
)


class IsOwnerOrStaff(permissions.BasePermission):
    """Allow access to ticket owner or staff users."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


@extend_schema_view(
    get=extend_schema(
        summary="List support tickets",
        description="Returns the authenticated user's tickets. Admin can see all tickets.",
        tags=["Support"],
    ),
    post=extend_schema(
        summary="Create a new support ticket",
        description="Create a ticket with a subject and initial message.",
        tags=["Support"],
        examples=[
            OpenApiExample(
                "Create ticket",
                value={
                    "subject": "Order not delivered",
                    "message": "Hi, my order has not arrived yet.",
                },
            )
        ],
    ),
)
class TicketListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/tickets/ — List user's tickets
    POST /api/tickets/ — Create ticket with first message
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateTicketSerializer
        return TicketListSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Ticket.objects.all()
        return Ticket.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = CreateTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ticket = Ticket.objects.create(
            user=request.user,
            subject=serializer.validated_data["subject"],
        )
        TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=serializer.validated_data["message"],
        )

        return Response(
            TicketDetailSerializer(ticket).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        summary="Get ticket detail with messages",
        description="Returns full ticket details including all messages. Only owner or staff can access.",
        tags=["Support"],
    )
)
class TicketDetailView(generics.RetrieveAPIView):
    """GET /api/tickets/{id}/ — Ticket detail with messages (owner or staff)."""

    serializer_class = TicketDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Ticket.objects.all()
        return Ticket.objects.filter(user=self.request.user)


@extend_schema_view(
    post=extend_schema(
        summary="Add message to ticket",
        description=(
            "Send a message in a support ticket. "
            "When a staff member replies, the ticket status automatically changes to `answered`."
        ),
        tags=["Support"],
    )
)
class TicketMessageCreateView(APIView):
    """POST /api/tickets/{id}/messages/ — Add message to ticket."""

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]

    def post(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return Response(
                {"error": "Ticket not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check permission
        if ticket.user != request.user and not request.user.is_staff:
            return Response(
                {"error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TicketMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=serializer.validated_data["message"],
        )

        # Auto-update status: staff response -> answered
        if request.user.is_staff:
            ticket.status = Ticket.Status.ANSWERED
            ticket.save(update_fields=["status"])

        return Response(
            TicketMessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    patch=extend_schema(
        summary="Update ticket status (staff only)",
        description="Change ticket status. Available statuses: `open`, `answered`, `closed`.",
        tags=["Support"],
    )
)
class TicketStatusUpdateView(APIView):
    """PATCH /api/tickets/{id}/status/ — Staff changes ticket status."""

    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    def patch(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return Response(
                {"error": "Ticket not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TicketStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ticket.status = serializer.validated_data["status"]
        ticket.save(update_fields=["status"])

        return Response(TicketDetailSerializer(ticket).data)
