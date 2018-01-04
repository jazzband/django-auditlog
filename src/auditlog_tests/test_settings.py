"""
Settings file for the Auditlog test suite.
"""
import django

SECRET_KEY = 'test'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'auditlog',
    'auditlog_tests',
    'multiselectfield',
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware'
    'auditlog.middleware.AuditlogMiddleware',
)

if django.VERSION <= (1, 9):
    POSTGRES_DRIVER = 'django.db.backends.postgresql_psycopg2'
else:
    POSTGRES_DRIVER = 'django.db.backends.postgresql'

DATABASE_ROUTERS = ['auditlog_tests.router.PostgresRouter']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'auditlog_tests.db',
    },
    'postgres': {
        'ENGINE': POSTGRES_DRIVER,
        'NAME': 'auditlog_tests_db',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

ROOT_URLCONF = []

USE_TZ = True
