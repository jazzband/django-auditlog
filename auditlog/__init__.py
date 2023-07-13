try:
    from importlib.metadata import version  # New in Python 3.8
except ImportError:
    from pkg_resources import (  # from setuptools, deprecated
        DistributionNotFound,
        get_distribution,
    )

    try:
        __version__ = get_distribution("django-auditlog").version
    except DistributionNotFound:
        # package is not installed
        pass
else:
    __version__ = version("django-auditlog")
