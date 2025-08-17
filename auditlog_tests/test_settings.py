"""
Settings file for the Auditlog test suite.
"""

import os

DEBUG = True

SECRET_KEY = "test"

TEST_DB_BACKEND = os.getenv("TEST_DB_BACKEND", "sqlite3")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.admin",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "auditlog",
    "test_app",
]


MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
]

if TEST_DB_BACKEND == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv(
                "TEST_DB_NAME", "auditlog" + os.environ.get("TOX_PARALLEL_ENV", "")
            ),
            "USER": os.getenv("TEST_DB_USER", "postgres"),
            "PASSWORD": os.getenv("TEST_DB_PASS", ""),
            "HOST": os.getenv("TEST_DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("TEST_DB_PORT", "5432"),
        }
    }
elif TEST_DB_BACKEND == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv(
                "TEST_DB_NAME", "auditlog" + os.environ.get("TOX_PARALLEL_ENV", "")
            ),
            "USER": os.getenv("TEST_DB_USER", "root"),
            "PASSWORD": os.getenv("TEST_DB_PASS", ""),
            "HOST": os.getenv("TEST_DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("TEST_DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
elif TEST_DB_BACKEND == "sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.getenv(
                "TEST_DB_NAME",
                (
                    ":memory:"
                    if os.getenv("TOX_PARALLEL_ENV")
                    else "test_auditlog.sqlite3"
                ),
            ),
        }
    }
else:
    raise ValueError(f"Unsupported database backend: {TEST_DB_BACKEND}")

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

ROOT_URLCONF = "test_app.urls"

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
