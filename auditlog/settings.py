from django.conf import settings

ENABLE_ELLIPSIS = getattr(settings, "AUDITLOG_ENABLE_ELLIPSIS", True)
