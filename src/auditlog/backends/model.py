import json

from auditlog.models import LogEntry

from .base import AuditBackend


class ModelBackend(AuditBackend):
    """Model based backend for creation of audit log entries."""

    def create_log(self, action, instance, changes, **kwargs):
        """Creates a new LogEntry model instance for the given action and instance"""
        return LogEntry.objects.log_create(
            instance=instance,
            action=action,
            changes=json.dumps(changes),
            **kwargs)
