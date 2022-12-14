import uuid

from django.conf import settings

# Register all models when set to True
settings.AUDITLOG_INCLUDE_ALL_MODELS = getattr(
    settings, "AUDITLOG_INCLUDE_ALL_MODELS", False
)

# Exclude models in registration process
# It will be considered when `AUDITLOG_INCLUDE_ALL_MODELS` is True
settings.AUDITLOG_EXCLUDE_TRACKING_MODELS = getattr(
    settings, "AUDITLOG_EXCLUDE_TRACKING_MODELS", ()
)

# Register models and define their logging behaviour
settings.AUDITLOG_INCLUDE_TRACKING_MODELS = getattr(
    settings, "AUDITLOG_INCLUDE_TRACKING_MODELS", ()
)

# Disable on raw save to avoid logging imports and similar
settings.AUDITLOG_DISABLE_ON_RAW_SAVE = getattr(
    settings, "AUDITLOG_DISABLE_ON_RAW_SAVE", False
)

# CID

settings.AUDITLOG_STORE_CID = getattr(settings, "AUDITLOG_STORE_CID", True)
settings.AUDITLOG_CID_HEADER = getattr(
    settings, "AUDITLOG_CID_HEADER", "x-correlation-id"
)
settings.AUDITLOG_CID_GENERATOR = getattr(
    settings, "AUDITLOG_CID_GENERATOR", uuid.uuid4
)
settings.AUDITLOG_CID_RETRIEVER = getattr(settings, "AUDITLOG_CID_RETRIEVER", None)
