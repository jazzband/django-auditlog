"""
Settings file for the Auditlog test suite.
"""
import os

DEBUG = True

SECRET_KEY = "test"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.admin",
    "django.contrib.staticfiles",
    "auditlog",
    "auditlog_tests",
]

MIDDLEWARE = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("TEST_DB_NAME", "auditlog_tests_db"),
        "USER": os.getenv("TEST_DB_USER", "postgres"),
        "PASSWORD": os.getenv("TEST_DB_PASS", ""),
        "HOST": os.getenv("TEST_DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("TEST_DB_PORT", "5432"),
    }
}

TEMPLATES = [
    {
        "APP_DIRS": True,
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    },
]

STATIC_URL = "/static/"

ROOT_URLCONF = "auditlog_tests.urls"

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


AUDITLOG_INCLUDE_ALL_MODELS = False
AUDITLOG_INCLUDE_TRACKING_MODELS = (
    "auditlog_tests.SimpleModel",
    {
        "model": "auditlog_tests.SimpleExcludeModel",
        "exclude_fields": ["text"],
    },
    {
        "model": "auditlog_tests.SimpleIncludeModel",
        "include_fields": ["label"],
    },
    {
        "model": "auditlog_tests.SimpleMappingModel",
        "mapping_fields": {"sku": "Product No."},
    },
    {
        "model": "auditlog_tests.SimpleMaskedModel",
        "mask_fields": ["address"],
    },
)
AUDITLOG_EXCLUDE_TRACKING_MODELS = ()
