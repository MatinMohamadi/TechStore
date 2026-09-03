from django.contrib import admin

from .models import Ticket, TicketMessage


class TicketMessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ["sender", "message", "created_at"]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "subject", "status", "created_at", "updated_at"]
    list_filter = ["status"]
    search_fields = ["subject", "user__email"]
    readonly_fields = ["user", "subject", "created_at", "updated_at"]
    inlines = [TicketMessageInline]


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ["ticket", "sender", "message_preview", "created_at"]
    search_fields = ["message"]

    def message_preview(self, obj):
        return obj.message[:80]
