"""
This code is heavily influenced by https://github.com/Polyconseil/django-cid

Copyright (c) 2016, Snowball One
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.
* Neither the name of CID nor the names of its contributors may be used to
endorse or promote products derived from this software without specific prior
written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from contextvars import ContextVar
from typing import Any, Callable, Optional, Union

from django.conf import settings
from django.http import HttpRequest
from django.utils.module_loading import import_string

correlation_id = ContextVar("auditlog_correlation_id", default=None)


def generate_cid(request: Optional[HttpRequest] = None) -> str:
    generator: Union[
        Callable[[], Any], Callable[[HttpRequest], Any]
    ] = settings.AUDITLOG_CID_GENERATOR
    if not generator:
        return ""
    try:
        cid = generator()
    except TypeError:
        # this is for when the user wants to do a more complex cid implementation
        cid = generator(request)
    return str(cid)


def set_cid(request: Optional[HttpRequest] = None) -> str:
    if not settings.AUDITLOG_STORE_CID:
        correlation_id.set(None)

    header = settings.AUDITLOG_CID_HEADER

    if header and header in getattr(request, "headers", {}):
        # todo: should we check META here instead of headers?
        cid = request.headers.get(header)
    else:
        cid = generate_cid(request)

    correlation_id.set(cid)
    return cid


def _get_cid() -> str:
    cid = correlation_id.get()
    if cid is None and settings.AUDITLOG_CID_GENERATOR:
        cid = set_cid()
    return cid


def _resolve_get_cid() -> Callable:
    method = settings.AUDITLOG_CID_RETRIEVER
    if not method:
        return _get_cid

    if callable(method):
        return method

    return import_string(method)


get_cid: Callable[..., str] = _resolve_get_cid()
