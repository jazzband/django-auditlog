from __future__ import annotations

from importlib.metadata import version

from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

__version__ = version("django-auditlog")


def get_logentry_model():
    try:
        return django_apps.get_model(
            settings.AUDITLOG_LOGENTRY_MODEL, require_ready=False
        )
    except ValueError:
        raise ImproperlyConfigured(
            "AUDITLOG_ENTRY_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "AUDITLOG_LOGENTRY_MODEL refers to model '%s' that has not been installed"
            % settings.AUDITLOG_LOGENTRY_MODEL
        )
