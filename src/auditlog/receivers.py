from __future__ import unicode_literals

import json

from auditlog.diff import model_instance_diff
from auditlog.models import LogEntry

try:
    import opentracing
except ImportError:
    opentracing = None


def log_create(sender, instance, created, **kwargs):
    """
    Signal receiver that creates a log entry when a model instance is first saved to the database.

    Direct use is discouraged, connect your model through :py:func:`auditlog.registry.register` instead.
    """
    if created:
        if opentracing:
            tracing_span = opentracing.global_tracer().start_active_span(
                'django-auditlog.create.{}'.format(sender._meta.label)
            )
        else:
            tracing_span = None

        try:
            changes = model_instance_diff(None, instance)

            log_entry = LogEntry.objects.log_create(
                instance,
                action=LogEntry.Action.CREATE,
                changes=json.dumps(changes),
            )
        finally:
            if tracing_span:
                tracing_span.close()


def log_update(sender, instance, **kwargs):
    """
    Signal receiver that creates a log entry when a model instance is changed and saved to the database.

    Direct use is discouraged, connect your model through :py:func:`auditlog.registry.register` instead.
    """
    if instance.pk is not None:
        if opentracing:
            tracing_span = opentracing.global_tracer().start_active_span(
                'django-auditlog.update.{}'.format(sender._meta.label),
            )
        else:
            tracing_span = None

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
        finally:
            if tracing_span:
                tracing_span.close()


def log_delete(sender, instance, **kwargs):
    """
    Signal receiver that creates a log entry when a model instance is deleted from the database.

    Direct use is discouraged, connect your model through :py:func:`auditlog.registry.register` instead.
    """
    if instance.pk is not None:
        if opentracing:
            tracing_span = opentracing.global_tracer().start_active_span(
                'django-auditlog.delete.{}'.format(sender._meta.label),
            )
        else:
            tracing_span = None

        try:
            changes = model_instance_diff(instance, None)

            log_entry = LogEntry.objects.log_create(
                instance,
                action=LogEntry.Action.DELETE,
                changes=json.dumps(changes),
            )
        finally:
            if tracing_span:
                tracing_span.close()
