import json

from auditlog.diff import model_instance_diff
from auditlog.models import LogEntry
from auditlog.signals import LogAction, post_log, pre_log


def log_create(sender, instance, created, **kwargs):
    """
    Signal receiver that creates a log entry when a model instance is first saved to the database.

    Direct use is discouraged, connect your model through :py:func:`auditlog.registry.register` instead.
    """
    if created:
        pre_log_results = pre_log.send(
            sender,
            instance=instance,
            action=LogAction.CREATE,
        )
        error = None
        try:
            changes = model_instance_diff(None, instance)

            LogEntry.objects.log_create(
                instance,
                action=LogEntry.Action.CREATE,
                changes=json.dumps(changes),
            )
        except Exception as e:
            error = e
        finally:
            post_log.send(
                sender,
                instance=instance,
                action=LogAction.CREATE,
                error=error,
                pre_log_results=pre_log_results,
            )
            if error:
                raise error


def log_update(sender, instance, **kwargs):
    """
    Signal receiver that creates a log entry when a model instance is changed and saved to the database.

    Direct use is discouraged, connect your model through :py:func:`auditlog.registry.register` instead.
    """
    if instance.pk is not None:
        pre_log_results = pre_log.send(
            sender,
            instance=instance,
            action=LogAction.UPDATE,
        )

        error = None
        try:
            old = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            pass
        else:
            try:
                new = instance

                changes = model_instance_diff(old, new)

                # Log an entry only if there are changes
                if changes:
                    LogEntry.objects.log_create(
                        instance,
                        action=LogEntry.Action.UPDATE,
                        changes=json.dumps(changes),
                    )
            except Exception as e:
                error = e
        finally:
            post_log.send(
                sender,
                instance=instance,
                action=LogAction.UPDATE,
                error=error,
                pre_log_results=pre_log_results,
            )
            if error:
                raise error


def log_delete(sender, instance, **kwargs):
    """
    Signal receiver that creates a log entry when a model instance is deleted from the database.

    Direct use is discouraged, connect your model through :py:func:`auditlog.registry.register` instead.
    """
    if instance.pk is not None:
        pre_log_results = pre_log.send(
            sender,
            instance=instance,
            action=LogAction.DELETE,
        )

        error = None
        try:
            changes = model_instance_diff(instance, None)

            LogEntry.objects.log_create(
                instance,
                action=LogEntry.Action.DELETE,
                changes=json.dumps(changes),
            )
        except Exception as e:
            error = e
        finally:
            post_log.send(
                sender,
                instance=instance,
                action=LogAction.DELETE,
                error=error,
                pre_log_results=pre_log_results,
            )
            if error:
                raise error

