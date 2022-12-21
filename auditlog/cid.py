from contextvars import ContextVar
from typing import Optional

from django.conf import settings
from django.http import HttpRequest
from django.utils.module_loading import import_string

correlation_id = ContextVar("auditlog_correlation_id", default=None)


def set_cid(request: Optional[HttpRequest] = None) -> None:
    """
    A function to read the cid from a request.
    If the header is not in the request, then we set it to `None`.

    Note: we look for the header in `request.headers` and `request.META`.

    :param request: The request to get the cid from.
    :return: None
    """
    cid = None
    header = settings.AUDITLOG_CID_HEADER

    if header and request and header in request.headers or header in request.META:
        cid = request.headers.get(header)

    # in theory, we shouldn't have to set the cid back to None because each request should be in a new thread.
    # however, this was causing some tests to fail.
    correlation_id.set(cid)


def _get_cid() -> Optional[str]:
    return correlation_id.get()


def get_cid() -> Optional[str]:
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
