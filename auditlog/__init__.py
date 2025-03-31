from __future__ import annotations

from importlib.metadata import version
from typing import TYPE_CHECKING

from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

if TYPE_CHECKING:
    from auditlog.models import AbstractLogEntry

__version__ = version("django-auditlog")


def get_logentry_model() -> type[AbstractLogEntry]:
    """
    Return the LogEntry model that is active in this project.
    """
    try:
        return django_apps.get_model(
            settings.AUDITLOG_LOGENTRY_MODEL, require_ready=False
        )
    except ValueError:
        raise ImproperlyConfigured(
            "AUDITLOG_LOGENTRY_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "AUDITLOG_LOGENTRY_MODEL refers to model '%s' that has not been installed"
            % settings.AUDITLOG_LOGENTRY_MODEL
        )
