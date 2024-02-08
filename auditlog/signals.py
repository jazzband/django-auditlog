import django.dispatch

accessed = django.dispatch.Signal()


pre_log = django.dispatch.Signal()
"""
Whenever an audit log entry is written, this signal
is sent before writing the log.
Keyword arguments sent with this signal:

:param class sender:
    The model class that's being audited.

:param Any instance:
    The actual instance that's being audited.

:param Action action:
    The action on the model resulting in an
    audit log entry. Type: :class:`auditlog.models.LogEntry.Action`

The receivers' return values are sent to any :func:`post_log`
signal receivers, with one exception: if any receiver returns False,
no logging will be made. This can be useful if logging should be
conditionally enabled / disabled
"""

post_log = django.dispatch.Signal()
"""
Whenever an audit log entry is written, this signal
is sent after writing the log.
This signal is also fired when there is an error in creating the log.

Keyword arguments sent with this signal:

:param class sender:
    The model class that's being audited.

:param Any instance:
    The actual instance that's being audited.

:param Action action:
    The action on the model resulting in an
    audit log entry. Type: :class:`auditlog.models.LogEntry.Action`

:param Optional[dict] changes:
    The changes that were logged. If there was en error while determining the changes,
    this will be None. In some cases, such as when logging access to the instance,
    the changes will be an empty dict.

:param Optional[LogEntry] log_entry:
    The log entry that was created and stored in the database. If there was an error,
    this will be None.

:param bool log_created:
    Was the log actually created?
    This could be false if there was an error in creating the log.

:param Optional[Exception] error:
    The error, if one occurred while saving the audit log entry. ``None``,
    otherwise

:param List[Tuple[method,Any]] pre_log_results:
    List of tuple pairs ``[(pre_log_receiver, pre_log_response)]``, where
    ``pre_log_receiver`` is the receiver method, and ``pre_log_response`` is the
    corresponding response of that method. If there are no :const:`pre_log` receivers,
    then the list will be empty. ``pre_log_receiver`` is guaranteed to be
    non-null, but ``pre_log_response`` may be ``None``. This depends on the corresponding
    ``pre_log_receiver``'s return value.
"""
