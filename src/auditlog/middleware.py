from django.conf import settings
from django.db.models.signals import pre_save
from django.utils.functional import curry
from django.db.models.loading import get_model

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

        set_actor = curry(self.set_actor, user)
        pre_save.connect(set_actor, sender=LogEntry, dispatch_uid=(self.__class__, request), weak=False)

    def process_response(self, request, response):
        pre_save.disconnect(dispatch_uid=(self.__class__, request))
        return response

    def set_actor(self, user, sender, instance, **kwargs):
        try:
            app_label, model_name = settings.AUTH_USER_MODEL.split('.')
            auth_user_model = get_model(app_label, model_name)
        except:
            auth_user_model = get_model('auth', 'user')
        if sender == LogEntry and isinstance(user, auth_user_model) and instance.actor is None:
            instance.actor = user
