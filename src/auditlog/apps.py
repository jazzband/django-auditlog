from __future__ import unicode_literals

from django.apps import AppConfig


class AuditlogConfig(AppConfig):
    name = 'auditlog'
    verbose_name = "Audit log"

    def ready(self):
        import jsonfield_compat
        jsonfield_compat.register_app(self)
