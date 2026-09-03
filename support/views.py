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


class TicketDetailView(generics.RetrieveAPIView):
    """GET /api/tickets/{id}/ — Ticket detail with messages (owner or staff)."""

    serializer_class = TicketDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Ticket.objects.all()
        return Ticket.objects.filter(user=self.request.user)


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
