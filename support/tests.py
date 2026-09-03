from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Ticket, TicketMessage

User = get_user_model()


class TicketAccessTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="support@test.com", password="TestPass123!"
        )
        self.other = User.objects.create_user(
            email="other@test.com", password="TestPass123!"
        )
        self.admin = User.objects.create_superuser(
            email="admin@test.com", password="Admin123!"
        )

    def test_create_ticket(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            "/api/tickets/",
            {"subject": "Delivery problem", "message": "My order hasn't arrived yet."},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["subject"], "Delivery problem")
        self.assertEqual(resp.data["status"], "open")
        self.assertEqual(len(resp.data["messages"]), 1)

    def test_user_lists_own_tickets(self):
        Ticket.objects.create(user=self.user, subject="Ticket 1")
        Ticket.objects.create(user=self.other, subject="Ticket 2")
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/tickets/")
        self.assertEqual(resp.data["count"], 1)

    def test_admin_lists_all_tickets(self):
        Ticket.objects.create(user=self.user, subject="Ticket 1")
        Ticket.objects.create(user=self.other, subject="Ticket 2")
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get("/api/tickets/")
        self.assertEqual(resp.data["count"], 2)

    def test_user_cannot_see_other_ticket(self):
        ticket = Ticket.objects.create(user=self.other, subject="Secret")
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"/api/tickets/{ticket.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_see_any_ticket(self):
        ticket = Ticket.objects.create(user=self.user, subject="User ticket")
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(f"/api/tickets/{ticket.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_add_message(self):
        ticket = Ticket.objects.create(user=self.user, subject="Help")
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            f"/api/tickets/{ticket.id}/messages/",
            {"message": "Any update?"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_staff_message_updates_status_to_answered(self):
        ticket = Ticket.objects.create(user=self.user, subject="Help")
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            f"/api/tickets/{ticket.id}/messages/",
            {"message": "We are looking into it."},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "answered")

    def test_staff_change_status(self):
        ticket = Ticket.objects.create(user=self.user, subject="Done")
        self.client.force_authenticate(user=self.admin)
        resp = self.client.patch(
            f"/api/tickets/{ticket.id}/status/",
            {"status": "closed"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "closed")

    def test_user_cannot_change_status(self):
        ticket = Ticket.objects.create(user=self.user, subject="My ticket")
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            f"/api/tickets/{ticket.id}/status/",
            {"status": "closed"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
