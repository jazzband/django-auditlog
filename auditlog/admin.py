from django.conf import settings
from django.contrib import admin
from django.core.paginator import Paginator
from django.utils.functional import cached_property

from auditlog.count import limit_query_time
from auditlog.filters import (
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


class LogEntryAdmin(admin.ModelAdmin, LogEntryAdminMixin):
    list_display = ["created", "resource_url", "action", "msg_short", "user_url"]
    search_fields = [
        "timestamp",
        "object_repr",
        "changes",
        "actor__first_name",
        "actor__last_name",
    ]
    list_filter = [
        "action",
        ShortActorFilter,
        ResourceTypeFilter,
        FieldFilter,
        ("timestamp", get_timestamp_filter()),
    ]
    readonly_fields = ["created", "resource_url", "action", "user_url", "msg"]
    fieldsets = [
        (None, {"fields": ["created", "user_url", "resource_url"]}),
        ("Changes", {"fields": ["action", "msg"]}),
    ]
    list_select_related = ["actor", "content_type"]
    show_full_result_count = False
    paginator = TimeLimitedPaginator


admin.site.register(LogEntry, LogEntryAdmin)
