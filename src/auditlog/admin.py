from django.contrib import admin
from .models import LogEntry
from .mixins import LogEntryAdminMixin
from .filters import ResourceTypeFilter


class LogEntryAdmin(admin.ModelAdmin, LogEntryAdminMixin):
    list_display = ['created', 'content_type', 'resource_url', 'action', 'msg_short', 'user_url']
    search_fields = ['timestamp', 'object_repr', 'changes','additional_data']
    list_filter = ['action', ResourceTypeFilter, 'timestamp', 'actor']
    readonly_fields = ['created', 'remote_addr_url_w','resource_url', 'content_type', 'action', 'user_url', 'msg','additional_data']
    fieldsets = [
        (None, {'fields': ['created', 'user_url', 'remote_addr_url_w', 'content_type', 'resource_url']}),
        ('Changes', {'fields': ['action', 'msg','additional_data']}),
    ]
    list_per_page = 30

admin.site.register(LogEntry, LogEntryAdmin)
