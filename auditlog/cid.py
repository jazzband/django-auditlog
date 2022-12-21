from contextvars import ContextVar
from typing import Optional

from django.conf import settings
from django.http import HttpRequest
from django.utils.module_loading import import_string

correlation_id = ContextVar("auditlog_correlation_id", default=None)


def set_cid(request: Optional[HttpRequest] = None) -> None:
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
    method = settings.AUDITLOG_CID_GETTER
    if not method:
        return _get_cid()

    if callable(method):
        return method()

    return import_string(method)()
