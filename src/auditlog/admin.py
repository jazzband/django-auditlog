from django.contrib import admin
from .models import LogEntry

class LogEntryAdmin(admin.ModelAdmin):
        list_display = ('object_pk', 'object_repr', 'actor', 'action', 'changes', 'timestamp')

admin.site.register(LogEntry, LogEntryAdmin)

