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

# Exclude named fields across all models
settings.AUDITLOG_EXCLUDE_TRACKING_FIELDS = getattr(
    settings, "AUDITLOG_EXCLUDE_TRACKING_FIELDS", ()
)

# Disable on raw save to avoid logging imports and similar
settings.AUDITLOG_DISABLE_ON_RAW_SAVE = getattr(
    settings, "AUDITLOG_DISABLE_ON_RAW_SAVE", False
)

# CID

settings.AUDITLOG_CID_HEADER = getattr(
    settings, "AUDITLOG_CID_HEADER", "x-correlation-id"
)
settings.AUDITLOG_CID_GETTER = getattr(settings, "AUDITLOG_CID_GETTER", None)

# migration
settings.AUDITLOG_TWO_STEP_MIGRATION = getattr(
    settings, "AUDITLOG_TWO_STEP_MIGRATION", False
)
settings.AUDITLOG_USE_TEXT_CHANGES_IF_JSON_IS_NOT_PRESENT = getattr(
    settings, "AUDITLOG_USE_TEXT_CHANGES_IF_JSON_IS_NOT_PRESENT", False
)
