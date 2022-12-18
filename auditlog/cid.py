from contextvars import ContextVar
from typing import Optional, Union

from django.conf import settings
from django.http import HttpRequest
from django.utils.module_loading import import_string

correlation_id = ContextVar("auditlog_correlation_id", default=None)


def set_cid(request: Optional[HttpRequest] = None) -> None:
    header = settings.AUDITLOG_CID_HEADER

    if header and request and header in request.headers or header in request.META:
        cid = request.headers.get(header)
        correlation_id.set(cid)


def _get_cid() -> Union[str, None]:
    return correlation_id.get()


def get_cid() -> Union[str, None]:
    method = settings.AUDITLOG_CID_GETTER
    if not method:
        return _get_cid()

    if callable(method):
        return method()

    return import_string(method)()
