from django.utils.module_loading import import_string

from auditlog import settings


def get_audit_backend():
    """Returns an instantiated audit backend class"""
    return import_string(settings.AUDITLOG_BACKEND)()


auditlog_backend = get_audit_backend()
