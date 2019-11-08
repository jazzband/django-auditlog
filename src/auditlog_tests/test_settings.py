"""
Settings file for the Auditlog test suite.
"""
import os
import django

SECRET_KEY = 'test'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.admin',
    'auditlog',
    'auditlog_tests',
    'multiselectfield',
]

middlewares = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
)

if django.VERSION < (1, 10):
    MIDDLEWARE_CLASSES = middlewares
else:
    MIDDLEWARE = middlewares

if django.VERSION <= (1, 9):
    POSTGRES_DRIVER = 'django.db.backends.postgresql_psycopg2'
else:
    POSTGRES_DRIVER = 'django.db.backends.postgresql'

DATABASES = {
    'default': {
        'ENGINE': POSTGRES_DRIVER,
        'NAME': 'auditlog_tests_db',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

TEMPLATES = [
    {
        'APP_DIRS': True,
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ]
        },
    },
]

ROOT_URLCONF = 'auditlog_tests.urls'

USE_TZ = True
