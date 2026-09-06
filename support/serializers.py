from rest_framework import serializers

from .models import Ticket, TicketMessage


class TicketMessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.CharField(source="sender.email", read_only=True)
    is_staff = serializers.SerializerMethodField()

    class Meta:
        model = TicketMessage
        fields = ["id", "sender", "sender_email", "message", "is_staff", "created_at"]
        read_only_fields = ["id", "sender", "created_at"]

    def get_is_staff(self, obj):
        return obj.sender.is_staff


class TicketListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    messages_count = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "subject",
            "status",
            "messages_count",
            "last_message",
            "created_at",
            "updated_at",
        ]

    def get_last_message(self, obj):
        msg = obj.messages.order_by("-created_at").first()
        if msg:
            return {
                "message": msg.message[:100],
                "sender": msg.sender.email,
                "created_at": msg.created_at,
            }
        return None

    def get_messages_count(self, obj):
        return obj.messages.count()


class TicketDetailSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "user",
            "user_email",
            "subject",
            "status",
            "messages",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "status", "created_at", "updated_at"]


class CreateTicketSerializer(serializers.Serializer):
    """Serializer for creating a ticket with first message."""

    subject = serializers.CharField(max_length=300)
    message = serializers.CharField()


class TicketMessageCreateSerializer(serializers.Serializer):
    """Serializer for adding a message to a ticket."""

    message = serializers.CharField()


class TicketStatusSerializer(serializers.Serializer):
    """Serializer for staff to change ticket status."""

    status = serializers.ChoiceField(choices=Ticket.Status.choices)
