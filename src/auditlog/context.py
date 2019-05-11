import contextlib
import time
import threading

from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.utils.functional import curry

from auditlog.models import LogEntry

threadlocal = threading.local()


@contextlib.contextmanager
def set_actor(actor, remote_addr=None):
    """Connect a signal receiver with current user attached."""
    # Initialize thread local storage
    threadlocal.auditlog = {
        'signal_duid': ('set_actor', time.time()),
        'remote_addr': remote_addr,
    }

    # Connect signal for automatic logging
    set_actor = curry(_set_actor, user=actor, signal_duid=threadlocal.auditlog['signal_duid'])
    pre_save.connect(set_actor, sender=LogEntry, dispatch_uid=threadlocal.auditlog['signal_duid'], weak=False)

    try:
        yield

    finally:
        try:
            auditlog = threadlocal.auditlog
        except AttributeError:
            pass
        else:
            pre_save.disconnect(sender=LogEntry, dispatch_uid=auditlog['signal_duid'])


def _set_actor(user, sender, instance, signal_duid, **kwargs):
    """Signal receiver with an extra 'user' kwarg.

    This function becomes a valid signal receiver when it is curried with the actor.
    """
    try:
        auditlog = threadlocal.auditlog
    except AttributeError:
        pass
    else:
        if signal_duid != auditlog['signal_duid']:
            return
        auth_user_model = get_user_model()
        if sender == LogEntry and isinstance(user, auth_user_model) and instance.actor is None:
            instance.actor = user

        instance.remote_addr = auditlog['remote_addr']
