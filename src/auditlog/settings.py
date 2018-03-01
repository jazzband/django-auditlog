import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

AUDITLOG_BACKEND = getattr(settings, 'AUDITLOG_BACKEND', 'auditlog.backends.model.ModelBackend')
AUDITLOG_LOGGER = getattr(settings, 'AUDITLOG_LOGGER', 'audit.log')
AUDITLOG_LEVEL = getattr(settings, 'AUDITLOG_LEVEL', logging.INFO)


try:
    import auditlog.backends
except ImportError:
    raise ImproperlyConfigured('Invalid value for AUDITLOG_BACKEND.  Please specify a valid backend.')
