import contextlib

from auditlog.context import set_actor


class AuditlogMiddleware:
    """
    Middleware to couple the request's user to log items. This is accomplished by currying the
    signal receiver with the user from the request (or None if the user is not authenticated).
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):

        if request.META.get("HTTP_X_FORWARDED_FOR"):
            # In case of proxy, set 'original' address
            remote_addr = request.META.get("HTTP_X_FORWARDED_FOR").split(",")[0]
        else:
            remote_addr = request.META.get("REMOTE_ADDR")

        if hasattr(request, "user") and request.user.is_authenticated:
            context = set_actor(actor=request.user, remote_addr=remote_addr)
        else:
            context = contextlib.nullcontext()

        with context:
            return self.get_response(request)
