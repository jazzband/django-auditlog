import django
from pkg_resources import DistributionNotFound, get_distribution

try:
    __version__ = get_distribution("django-auditlog").version
except DistributionNotFound:
    # package is not installed
    pass

if django.VERSION < (3, 2):
    default_app_config = "auditlog.apps.AuditlogConfig"
