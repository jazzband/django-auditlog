from django.contrib import admin

from .filters import ResourceTypeFilter
from .mixins import LogEntryAdminMixin
from .models import LogEntry


class LogEntryAdmin(admin.ModelAdmin, LogEntryAdminMixin):
    list_display = ["created", "resource_url", "action", "msg_short", "user_url"]
    search_fields = [
        "timestamp",
        "object_repr",
        "changes",
        "actor__first_name",
        "actor__last_name",
    ]
    list_filter = ["action", ResourceTypeFilter]
    readonly_fields = ["created", "resource_url", "action", "user_url", "msg"]
    fieldsets = [
        (None, {"fields": ["created", "user_url", "resource_url"]}),
        ("Changes", {"fields": ["action", "msg"]}),
    ]


admin.site.register(LogEntry, LogEntryAdmin)
