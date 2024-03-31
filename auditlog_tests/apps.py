from django.apps import AppConfig


class AuditlogTestConfig(AppConfig):
    name = "auditlog_tests"

    def ready(self) -> None:
        from auditlog_tests.test_registry import (
            create_only_auditlog,
            update_only_auditlog,
        )

        create_only_auditlog.register_from_settings()
        update_only_auditlog.register_from_settings()
