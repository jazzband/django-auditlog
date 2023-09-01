from functools import cached_property

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _

from auditlog.count import limit_query_time
from auditlog.filters import (
    CIDFilter,
    FieldFilter,
    ResourceTypeFilter,
    ShortActorFilter,
    get_timestamp_filter,
)
from auditlog.mixins import LogEntryAdminMixin
from auditlog.models import LogEntry


class TimeLimitedPaginator(Paginator):
    """A PostgreSQL-specific paginator with a hard time limit for total count of pages."""

    @cached_property
    @limit_query_time(
        getattr(settings, "AUDITLOG_PAGINATOR_TIMEOUT", 500), default=100000
    )
    def count(self):
        return super().count


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin, LogEntryAdminMixin):
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
        "actor__first_name",
        "actor__last_name",
        f"actor__{get_user_model().USERNAME_FIELD}",
    ]
    list_filter = [
        "action",
        ShortActorFilter,
        ResourceTypeFilter,
        FieldFilter,
        ("timestamp", get_timestamp_filter()),
        CIDFilter,
    ]
    readonly_fields = ["created", "resource_url", "action", "user_url", "msg"]
    fieldsets = [
        (None, {"fields": ["created", "user_url", "resource_url", "cid"]}),
        (_("Changes"), {"fields": ["action", "msg"]}),
    ]
    list_select_related = ["actor", "content_type"]
    show_full_result_count = False
    paginator = TimeLimitedPaginator

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @cached_property
    def _own_url_names(self):
        return [pattern.name for pattern in self.urls if pattern.name]

    def has_delete_permission(self, request, obj=None):
        if (
            request.resolver_match
            and request.resolver_match.url_name not in self._own_url_names
        ):
            # only allow cascade delete to satisfy delete_related flag
            return super().has_delete_permission(request, obj)
        return False

    def get_queryset(self, request):
        self.request = request
        return super().get_queryset(request=request)
