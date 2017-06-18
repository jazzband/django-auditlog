from django.contrib import admin
from .models import LogEntry
from .mixins import LogEntryAdminMixin
from .filters import ResourceTypeFilter


class LogEntryAdmin(admin.ModelAdmin, LogEntryAdminMixin):
    list_display = ['created', 'content_type', 'resource_url', 'action', 'msg_short', 'user_url']
    search_fields = ['timestamp', 'object_repr', 'changes', 'actor__first_name', 'actor__last_name']
    list_filter = ['action', ResourceTypeFilter, 'actor','timestamp']
    readonly_fields = ['created', 'resource_url', 'content_type', 'action', 'user_url', 'msg']
    fieldsets = [
        (None, {'fields': ['created', 'user_url', 'content_type', 'resource_url']}),
        ('Changes', {'fields': ['action', 'msg']}),
    ]


admin.site.register(LogEntry, LogEntryAdmin)
