from django.conf import settings
from django.contrib import admin
from django.core.paginator import Paginator
from django.db import connection, transaction, OperationalError
from django.utils.functional import cached_property

from .models import LogEntry
from .mixins import LogEntryAdminMixin
from .filters import ResourceTypeFilter, FieldFilter


class TimeLimitedPaginator(Paginator):
    """A PostgreSQL-specific paginator with a hard time limit for total count of pages.

    Courtesy of https://medium.com/@hakibenita/optimizing-django-admin-paginator-53c4eb6bfca3
    """
    DEFAULT_PAGE_COUNT = 10000

    @cached_property
    def count(self):
        timeout = getattr(settings, 'AUDITLOG_PAGINATOR_TIMEOUT', 500)  # ms
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute('SET LOCAL statement_timeout TO %s;', (timeout,))
            try:
                return super().count
            except OperationalError:
                return self.per_page * self.DEFAULT_PAGE_COUNT


class LogEntryAdmin(admin.ModelAdmin, LogEntryAdminMixin):
    list_display = ['created', 'resource_url', 'action', 'msg_short', 'user_url']
    search_fields = ['timestamp', 'object_repr', 'changes', 'actor__first_name', 'actor__last_name']
    list_filter = ['action', ResourceTypeFilter, FieldFilter]
    readonly_fields = ['created', 'resource_url', 'action', 'user_url', 'msg']
    fieldsets = [
        (None, {'fields': ['created', 'user_url', 'resource_url']}),
        ('Changes', {'fields': ['action', 'msg']}),
    ]
    list_select_related = ['actor', 'content_type']
    show_full_result_count = False
    paginator = TimeLimitedPaginator


admin.site.register(LogEntry, LogEntryAdmin)
