from functools import wraps

from django.conf import settings

from auditlog.context import threadlocal
from auditlog.diff import model_instance_diff
from auditlog.models import LogEntry
from auditlog.signals import post_log, pre_log


def check_disable(signal_handler):
    """
    Decorator that passes along disabled in kwargs if any of the following is true:
    - 'auditlog_disabled' from threadlocal is true
    - raw = True and AUDITLOG_DISABLE_ON_RAW_SAVE is True
    """

    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        if not getattr(threadlocal, "auditlog_disabled", False) and not (
            kwargs.get("raw") and settings.AUDITLOG_DISABLE_ON_RAW_SAVE
        ):
            signal_handler(*args, **kwargs)

    return wrapper


@check_disable
def log_create(sender, instance, created, **kwargs):
    """
    Signal receiver that creates a log entry when a model instance is first saved to the database.

    Direct use is discouraged, connect your model through :py:func:`auditlog.registry.register` instead.
    """
    if created:
        _create_log_entry(
            action=LogEntry.Action.CREATE,
            instance=instance,
            sender=sender,
            diff_old=None,
            diff_new=instance,
        )


@check_disable
def log_update(sender, instance, **kwargs):
    """
    Signal receiver that creates a log entry when a model instance is changed and saved to the database.

    Direct use is discouraged, connect your model through :py:func:`auditlog.registry.register` instead.
    """
    if instance.pk is not None:
        update_fields = kwargs.get("update_fields", None)
        old = sender.objects.filter(pk=instance.pk).first()
        _create_log_entry(
            action=LogEntry.Action.UPDATE,
            instance=instance,
            sender=sender,
            diff_old=old,
            diff_new=instance,
            fields_to_check=update_fields,
        )


@check_disable
def log_delete(sender, instance, **kwargs):
    """
    Signal receiver that creates a log entry when a model instance is deleted from the database.

    Direct use is discouraged, connect your model through :py:func:`auditlog.registry.register` instead.
    """
    if instance.pk is not None:
        _create_log_entry(
            action=LogEntry.Action.DELETE,
            instance=instance,
            sender=sender,
            diff_old=instance,
            diff_new=None,
        )


def log_access(sender, instance, **kwargs):
    """
    Signal receiver that creates a log entry when a model instance is accessed in a AccessLogDetailView.

    Direct use is discouraged, connect your model through :py:func:`auditlog.registry.register` instead.
    """
    if instance.pk is not None:
        _create_log_entry(
            action=LogEntry.Action.ACCESS,
            instance=instance,
            sender=sender,
            diff_old=None,
            diff_new=None,
            force_log=True,
        )


def _create_log_entry(
    action, instance, sender, diff_old, diff_new, fields_to_check=None, force_log=False
):
    pre_log_results = pre_log.send(
        sender,
        instance=instance,
        action=action,
    )
    error = None
    try:
        changes = model_instance_diff(
            diff_old, diff_new, fields_to_check=fields_to_check
        )

        if force_log or changes:
            LogEntry.objects.log_create(
                instance,
                action=action,
                changes=changes,
                force_log=force_log,
            )
    except BaseException as e:
        error = e
    finally:
        post_log.send(
            sender,
            instance=instance,
            action=action,
            error=error,
            pre_log_results=pre_log_results,
        )
        if error:
            raise error


def make_log_m2m_changes(field_name):
    """Return a handler for m2m_changed with field_name enclosed."""

    @check_disable
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
