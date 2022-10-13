from django.apps import AppConfig


class AuditlogConfig(AppConfig):
    name = "auditlog"
    verbose_name = "Audit log"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from auditlog.registry import auditlog

        auditlog.register_from_settings()
