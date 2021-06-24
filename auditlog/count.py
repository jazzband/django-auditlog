from django.db import connection, transaction, OperationalError


def limit_query_time(timeout, default=None):
    """A PostgreSQL-specific decorator with a hard time limit and a default return value.

    Timeout in milliseconds.

    Courtesy of https://medium.com/@hakibenita/optimizing-django-admin-paginator-53c4eb6bfca3
    """

    def decorator(function):
        def _limit_query_time(*args, **kwargs):
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout TO %s;", (timeout,))
                try:
                    return function(*args, **kwargs)
                except OperationalError:
                    return default

        return _limit_query_time

    return decorator
