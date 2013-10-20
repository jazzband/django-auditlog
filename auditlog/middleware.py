from django.db.models.signals import pre_save
from django.utils.functional import curry
from auditlog.models import LogEntry


class AuditLogMiddleware(object):
    """
    Middleware to couple the request's user to log items. This is accomplished by currying the signal receiver with the
    user from the request (or None if the user is not authenticated).
    """

    def process_request(self, request):
        if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated():
            user = request.user
        else:
            user = None

        insert_user = curry(self.insert_user, user)
        pre_save.connect(insert_user, sender=LogEntry, dispatch_uid=(self.__class__, request), weak=False)

    def process_response(self, request, response):
        pre_save.disconnect(dispatch_uid=(self.__class__, request))
        return response

    def insert_user(self, user, sender, instance, **kwargs):
        if sender == LogEntry and isinstance(instance, sender):
            instance.actor = user
