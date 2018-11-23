"""
Settings file for the Auditlog test suite.
"""
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

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
)

DATABASE_ROUTERS = ['auditlog_tests.router.PostgresRouter']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'auditlog_tests.db',
    },
    'postgres': {
        'ENGINE': 'django.db.backends.postgresql',
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
