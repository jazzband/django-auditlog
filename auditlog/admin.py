from django.contrib import admin
from django.contrib.auth import get_user_model

from auditlog.filters import ResourceTypeFilter
from auditlog.mixins import LogEntryAdminMixin
from auditlog.models import LogEntry

user_model = get_user_model()

user_model_fields = [field.name for field in user_model._meta.get_fields()]

has_first_and_last_name_fields = (
    "first_name" in user_model_fields and "last_name" in user_model_fields
)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin, LogEntryAdminMixin):
    list_select_related = ["content_type", "actor"]
    list_display = ["created", "resource_url", "action", "msg_short", "user_url"]
    search_fields = [
        "timestamp",
        "object_repr",
        "changes",
        f"actor__{user_model.USERNAME_FIELD}",
    ] + (
        ["actor__first_name", "actor__last_name"]
        if has_first_and_last_name_fields
        else []
    )
    list_filter = ["action", ResourceTypeFilter]
    readonly_fields = ["created", "resource_url", "action", "user_url", "msg"]
    fieldsets = [
        (None, {"fields": ["created", "user_url", "resource_url"]}),
        ("Changes", {"fields": ["action", "msg"]}),
    ]

    def has_add_permission(self, request):
        # As audit admin doesn't allow log creation from admin
        return False
