from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from auditlog.filters import CIDFilter, ResourceTypeFilter
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
    list_display = [
        "created",
        "resource_url",
        "action",
        "msg_short",
        "user_url",
        "cid_url",
    ]
    search_fields = [
        "timestamp",
        "object_repr",
        "changes",
        f"actor__{user_model.USERNAME_FIELD}",
    ] + (["actor__first_name", "actor__last_name"] if has_first_and_last_name_fields else [])
    list_filter = ["action", ResourceTypeFilter, CIDFilter]
    readonly_fields = ["created", "resource_url", "action", "user_url", "msg"]
    fieldsets = [
        (None, {"fields": ["created", "user_url", "resource_url", "cid"]}),
        (_("Changes"), {"fields": ["action", "msg"]}),
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        self.request = request
        return super().get_queryset(request=request)
