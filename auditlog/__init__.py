from pkg_resources import DistributionNotFound, get_distribution

try:
    __version__ = get_distribution("django-auditlog").version
except DistributionNotFound:
    # package is not installed
    pass

default_app_config = "auditlog.apps.AuditlogConfig"
