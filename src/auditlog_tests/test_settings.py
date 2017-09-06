"""
Settings file for the Auditlog test suite.
"""

SECRET_KEY = 'test'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'auditlog',
    'auditlog_tests',
    'multiselectfield',
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'auditlog_test.db',
    }
}

ROOT_URLCONF = []

USE_TZ = True
