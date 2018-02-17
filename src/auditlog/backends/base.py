from auditlog.diff import model_instance_diff
from auditlog.models import LogEntry


class AuditBackend(object):
    """Base backend for creation of audit log entries."""

    def log_create(self, instance, created, **kwargs):
        """Handle model creation logging"""
        if created:
            changes = model_instance_diff(None, instance)

            self.create_log(
                instance=instance,
                action=LogEntry.Action.CREATE,
                changes=changes,
                **kwargs)

    def log_update(self, instance, **kwargs):
        """Handle model update logging"""
        if instance.pk is not None:
            try:
                old = instance.__class__.objects.get(pk=instance.pk)
            except instance.__class__.DoesNotExist:
                pass
            else:
                new = instance

                changes = model_instance_diff(old, new)

                # Log an entry only if there are changes
                if changes:
                    self.create_log(
                        instance=instance,
                        action=LogEntry.Action.UPDATE,
                        changes=changes,
                        **kwargs)

    def log_delete(self, instance, **kwargs):
        """Handle model deletion logging"""
        if instance.pk is not None:
            changes = model_instance_diff(instance, None)

            self.create_log(
                instance=instance,
                action=LogEntry.Action.DELETE,
                changes=changes,
                **kwargs)

    def create_log(self, action, instance, changes, **kwargs):
        raise NotImplemented('Backend must implement a log create method')
