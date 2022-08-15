import json
from itertools import chain

from auditlog.diff import model_instance_diff
from auditlog.models import LogEntry

from django.conf import settings
from django.db.models import ForeignKey, OneToOneField, OneToOneRel


def log_create(sender, instance, created, **kwargs):
    """
    Signal receiver that creates a log entry when a model instance is first saved to the database.

    Direct use is discouraged, connect your model through :py:func:`auditlog.registry.register` instead.
    """
    if created:
        changes = model_instance_diff(None, instance)

        LogEntry.objects.log_create(
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
        update_fields = kwargs.get("update_fields", None)
        try:
            if settings.AUDITLOG_SELECT_RELATED_FIELDS:
                fk_fields = []
                for field in chain(sender._meta.fields, sender._meta.related_objects):
                    if isinstance(field, (ForeignKey, OneToOneField, OneToOneRel)):
                        if not update_fields or (update_fields and field.name in update_fields):
                            fk_fields.append(field.name)
                old = sender.objects.select_related(*fk_fields).get(pk=instance.pk)
            else:
                old = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            pass
        else:
            new = instance
            changes = model_instance_diff(old, new, fields_to_check=update_fields)

            # Log an entry only if there are changes
            if changes:
                LogEntry.objects.log_create(
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

        LogEntry.objects.log_create(
            instance,
            action=LogEntry.Action.DELETE,
            changes=json.dumps(changes),
        )


def make_log_m2m_changes(field_name):
    """Return a handler for m2m_changed with field_name enclosed."""

    def log_m2m_changes(signal, action, **kwargs):
        """Handle m2m_changed and call LogEntry.objects.log_m2m_changes as needed."""
        if action not in ["post_add", "post_clear", "post_remove"]:
            return

        if action == "post_clear":
            changed_queryset = kwargs["model"].objects.all()
        else:
            changed_queryset = kwargs["model"].objects.filter(pk__in=kwargs["pk_set"])

        if action in ["post_add"]:
            LogEntry.objects.log_m2m_changes(
                changed_queryset,
                kwargs["instance"],
                "add",
                field_name,
            )
        elif action in ["post_remove", "post_clear"]:
            LogEntry.objects.log_m2m_changes(
                changed_queryset,
                kwargs["instance"],
                "delete",
                field_name,
            )

    return log_m2m_changes
