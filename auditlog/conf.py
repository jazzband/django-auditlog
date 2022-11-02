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

# Do select_related on related fields to eliminate unnecessary queries
settings.AUDITLOG_SELECT_RELATED_FIELDS = getattr(
    settings, "AUDITLOG_SELECT_RELATED_FIELDS", False
)
