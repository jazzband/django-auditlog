from django.contrib import admin
from django.core.paginator import Paginator

from .models import LogEntry
from .mixins import LogEntryAdminMixin
from .filters import ResourceTypeFilter


class NoCountPaginator(Paginator):
    PAGE_COUNT = 10000  # a large number

    @property
    def count(self):
        return self.per_page * self.PAGE_COUNT


class LogEntryAdmin(admin.ModelAdmin, LogEntryAdminMixin):
    list_display = ['created', 'resource_url', 'action', 'msg_short', 'user_url']
    search_fields = ['timestamp', 'object_repr', 'changes', 'actor__first_name', 'actor__last_name']
    list_filter = ['action', ResourceTypeFilter]
    readonly_fields = ['created', 'resource_url', 'action', 'user_url', 'msg']
    fieldsets = [
        (None, {'fields': ['created', 'user_url', 'resource_url']}),
        ('Changes', {'fields': ['action', 'msg']}),
    ]
    list_select_related = ['actor', 'content_type']
    show_full_result_count = False
    paginator = NoCountPaginator


admin.site.register(LogEntry, LogEntryAdmin)
