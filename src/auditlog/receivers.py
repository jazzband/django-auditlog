from __future__ import unicode_literals

import json

from auditlog.diff import model_instance_diff
from auditlog.models import LogEntry


def log_create(sender, instance, created, **kwargs):
    """
    Signal receiver that creates a log entry when a model instance is first saved to the database.

    Direct use is discouraged, connect your model through :py:func:`auditlog.registry.register` instead.
    """
    if created:
        changes = model_instance_diff(None, instance)

        log_entry = LogEntry.objects.log_create(
            instance,
            action=LogEntry.Action.CREATE,
            changes=json.dumps(changes),
        )


def log_update(sender, instance, **kwargs):
    """
    Signal receiver that creates a log entry when a model instance is changed and saved to the database.

    Direct use is discouraged, connect your model through :py:func:`auditlog.registry.register` instead.
    """
    if instance.pk is not None:
        try:
            old = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            pass
        else:
            new = instance

            changes = model_instance_diff(old, new)

            # Log an entry only if there are changes
            if changes:
                log_entry = LogEntry.objects.log_create(
                    instance,
                    action=LogEntry.Action.UPDATE,
                    changes=json.dumps(changes),
                )


def log_delete(sender, instance, **kwargs):
    """
    Signal receiver that creates a log entry when a model instance is deleted from the database.

    Direct use is discouraged, connect your model through :py:func:`auditlog.registry.register` instead.
    """
    if instance.pk is not None:
        changes = model_instance_diff(instance, None)

        log_entry = LogEntry.objects.log_create(
            instance,
            action=LogEntry.Action.DELETE,
            changes=json.dumps(changes),
        )


def log_m2m_changes(signal, action, **kwargs):
    """
    m2m changes signal, used to log all changes to m2m relationships, used with m2m_changed.connect

    """
    m2m_signals = kwargs['sender']._map_signals
    if action in m2m_signals:
        if action == 'post_clear':
            changed_queryset = kwargs['model'].objects.all()
        else:
            changed_queryset = kwargs['model'].objects.filter(pk__in=kwargs['pk_set'])

        if changed_queryset is not None:
            if action == 'post_add':
                LogEntry.objects.log_m2m_changes(
                    changed_queryset,
                    kwargs['instance'],
                    LogEntry.Action.ADDED,
                )
            elif action == 'post_remove':
                LogEntry.objects.log_m2m_changes(
                    changed_queryset,
                    kwargs['instance'],
                    LogEntry.Action.DELETE,
                )
            elif action == 'post_clear':
                LogEntry.objects.log_m2m_changes(
                    changed_queryset,
                    kwargs['instance'],
                    LogEntry.Action.DELETE,
                )
