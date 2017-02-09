"""
Settings file for the Auditlog test suite.
"""

SECRET_KEY = 'test'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'auditlog',
    'auditlog_tests',
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'auditlog_tests.db',
    }
}

ROOT_URLCONF = []

USE_TZ = True
