from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuditlogConfig(AppConfig):
    """Default configuration for auditlog app."""

    name = "auditlog"
    label = "auditlog"
    verbose_name = _("Audit Log")
    default_auto_field = "django.db.models.AutoField"
