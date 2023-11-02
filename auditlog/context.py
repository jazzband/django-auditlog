import contextlib
import time
from contextvars import ContextVar
from functools import partial

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db.models.signals import pre_save

from auditlog.models import LogEntry

auditlog_value = ContextVar("auditlog_value")
auditlog_disabled = ContextVar("auditlog_disabled", default=False)


@contextlib.contextmanager
def set_actor(actor, remote_addr=None):
    yield from _set_logger_data(actor, {}, remote_addr)


@contextlib.contextmanager
def set_auditlog_custom_data(actor: User = None, remote_addr: str = None, **kwargs):
    yield from _set_logger_data(actor, kwargs, remote_addr)


def _set_logger_data(actor, kwargs, remote_addr):
    try:
        context_data = auditlog_value.get()
    except LookupError:
        context_data = {}
    actor = actor or context_data.get('actor')
    custom_data = context_data.get('custom_data', {})
    custom_data.update(kwargs)
    """Connect a signal receiver with current user attached."""
    context_data = {
        "signal_duid": ("set_auditlog_custom_data", time.time()),
        "remote_addr": remote_addr,
        "custom_data": custom_data,
    }
    if actor:
        context_data['actor'] = actor
    token = auditlog_value.set(context_data)
    # Connect signal for automatic logging
    set_auditlog_custom_data = partial(
        _set_auditlog_custom_data, user=actor, signal_duid=context_data["signal_duid"]
    )
    pre_save.connect(
        set_auditlog_custom_data,
        sender=LogEntry,
        dispatch_uid=context_data["signal_duid"],
        weak=False,
    )
    try:
        yield
    finally:
        try:
            auditlog = auditlog_value.get()
        except LookupError:
            pass
        else:
            pre_save.disconnect(sender=LogEntry, dispatch_uid=auditlog["signal_duid"])
            auditlog_value.reset(token)


def _set_auditlog_custom_data(user: User, sender, instance, signal_duid, **kwargs):
    """Signal receiver with extra 'user' and 'signal_duid' kwargs.

    This function becomes a valid signal receiver when it is curried with the actor and a dispatch id.
    """
    try:
        auditlog = auditlog_value.get()
    except LookupError:
        pass
    else:
        if signal_duid != auditlog["signal_duid"]:
            return
        auth_user_model = get_user_model()
        if (
            sender == LogEntry
            and isinstance(user, auth_user_model)
            and instance.actor is None
        ):
            instance.actor = user
            instance.actor_email = user.email
        instance.remote_addr = auditlog["remote_addr"]
        instance.custom_data = auditlog["custom_data"]


@contextlib.contextmanager
def disable_auditlog():
    token = auditlog_disabled.set(True)
    try:
        yield
    finally:
        try:
            auditlog_disabled.reset(token)
        except LookupError:
            pass
