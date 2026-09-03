from django.conf import settings
from django.db import models


class Ticket(models.Model):
    """Support ticket from a customer."""

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ANSWERED = "answered", "Answered"
        CLOSED = "closed", "Closed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets",
    )
    subject = models.CharField(max_length=300)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.id} {self.subject} ({self.status})"


class TicketMessage(models.Model):
    """A message within a support ticket."""

    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ticket_messages",
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ticket Message"
        verbose_name_plural = "Ticket Messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"Message by {self.sender.email} on Ticket #{self.ticket_id}"
