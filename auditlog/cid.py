from contextvars import ContextVar

from django.conf import settings
from django.http import HttpRequest
from django.utils.module_loading import import_string

correlation_id = ContextVar("auditlog_correlation_id", default=None)


def set_cid(request: HttpRequest | None = None) -> None:
    """
    A function to read the cid from a request.
    If the header is not in the request, then we set it to `None`.

    Note: we look for the value of `AUDITLOG_CID_HEADER` in `request.headers` and in `request.META`.

    This function doesn't do anything if the user is supplying their own `AUDITLOG_CID_GETTER`.

    :param request: The request to get the cid from.
    :return: None
    """
    if settings.AUDITLOG_CID_GETTER:
        return

    cid = None
    header = settings.AUDITLOG_CID_HEADER

    if header and request:
        if header in request.headers:
            cid = request.headers.get(header)
        elif header in request.META:
            cid = request.META.get(header)

    # Ideally, this line should be nested inside the if statement.
    # However, because the tests do not run requests in multiple threads,
    # we have to always set the value of the cid,
    # even if the request does not have the header present,
    # in which case it will be set to None
    correlation_id.set(cid)


def _get_cid() -> str | None:
    return correlation_id.get()


def get_cid() -> str | None:
    """
    Calls the cid getter function based on `settings.AUDITLOG_CID_GETTER`

    If the setting value is:

    * None: then it calls the default getter (which retrieves the value set in `set_cid`)
    * callable: then it calls the function
    * type(str): then it imports the function and then call it

    The result is then returned to the caller.

    If your custom getter does not depend on `set_header()`,
    then we recommend setting `settings.AUDITLOG_CID_GETTER` to `None`.

    :return: The correlation ID
    """
    method = settings.AUDITLOG_CID_GETTER
    if not method:
        return _get_cid()

    if callable(method):
        return method()

    return import_string(method)()
