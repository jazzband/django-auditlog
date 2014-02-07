import time

from django.conf import settings
from django.db.models.signals import pre_save
from django.utils.functional import curry
from django.db.models.loading import get_model
from auditlog.models import LogEntry


class AuditlogMiddleware(object):
    """
    Middleware to couple the request's user to log items. This is accomplished by currying the signal receiver with the
    user from the request (or None if the user is not authenticated).
    """

    def process_request(self, request):
        """
        Gets the current user from the request and prepares and connects a signal receiver with the user already
        attached to it.
        """
        if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated():
            user = request.user
        else:
            user = None

        request.auditlog_ts = time.time()
        set_actor = curry(self.set_actor, user)
        pre_save.connect(set_actor, sender=LogEntry, dispatch_uid=(self.__class__, request.auditlog_ts), weak=False)

    def process_response(self, request, response):
        """
        Disconnects the signal receiver to prevent it from staying active.
        """
        # Disconnecting the signal receiver is required because it will not be garbage collected (non-weak reference)
        pre_save.disconnect(sender=LogEntry, dispatch_uid=(self.__class__, request.auditlog_ts))

        return response

    def process_exception(self, request, exception):
        """
        Disconnects the signal receiver to prevent it from staying active in case of an exception.
        """
        pre_save.disconnect(sender=LogEntry, dispatch_uid=(self.__class__, request.auditlog_ts))

        return None

    @staticmethod
    def set_actor(user, sender, instance, **kwargs):
        """
        Signal receiver with an extra, required 'user' kwarg. This method becomes a real (valid) signal receiver when
        it is curried with the actor.
        """
        try:
            app_label, model_name = settings.AUTH_USER_MODEL.split('.')
            auth_user_model = get_model(app_label, model_name)
        except ValueError:
            auth_user_model = get_model('auth', 'user')
        if sender == LogEntry and isinstance(user, auth_user_model) and instance.actor is None:
            instance.actor = user
