from __future__ import unicode_literals

from django.db.models.signals import pre_save, post_save, post_delete
from django.db.models import Model


class AuditlogModelRegistry(object):
    """
    A registry that keeps track of the models that use Auditlog to track changes.
    """
    def __init__(self, create=True, update=True, delete=True, custom=None):
        from auditlog.receivers import log_create, log_update, log_delete

        self._registry = {}
        self._signals = {}

        if create:
            self._signals[post_save] = log_create
        if update:
            self._signals[pre_save] = log_update
        if delete:
            self._signals[post_delete] = log_delete

        if custom is not None:
            self._signals.update(custom)

    def register(self, model, **kwargs):
        """
        Register a model with auditlog. Auditlog will then track mutations on this model's instances.

        Kwargs:
          - `include_fields`: list of field names to include in diff
          - `exclude_fields`: list of field names to exclude in diff
        """
        if issubclass(model, Model):
            self._registry[model] = {
                'include_fields': kwargs.get('include_fields', []),
                'exclude_fields': kwargs.get('exclude_fields', []),
            }
            self._connect_signals(model)
        else:
            raise TypeError("Supplied model is not a valid model.")

    def contains(self, model):
        """
        Check if a model is registered with auditlog.
        """
        return model in self._registry

    def unregister(self, model):
        """
        Unregister a model with auditlog. This will not affect the database.
        """
        try:
            del self._registry[model]
        except KeyError:
            pass
        else:
            self._disconnect_signals(model)

    def _connect_signals(self, model):
        """
        Connect signals for the model.
        """
        for signal in self._signals:
            receiver = self._signals[signal]
            signal.connect(receiver, sender=model, dispatch_uid=self._dispatch_uid(signal, model))

    def _disconnect_signals(self, model):
        """
        Disconnect signals for the model.
        """
        for signal, receiver in self._signals:
            signal.disconnect(dispatch_uid=self._dispatch_uid(signal, model))

    def _dispatch_uid(self, signal, model):
        """
        Generate a dispatch_uid.
        """
        return (self.__class__, model, signal)

    def get_model_fields(self, model):
        return {
            'include_fields': self._registry[model]['include_fields'],
            'exclude_fields': self._registry[model]['exclude_fields'],
        }


class AuditLogModelRegistry(AuditlogModelRegistry):
    def __init__(self, *args, **kwargs):
        super(AuditLogModelRegistry, self).__init__(*args, **kwargs)
        raise DeprecationWarning("Use AuditlogModelRegistry instead of AuditLogModelRegistry, AuditLogModelRegistry will be removed in django-auditlog 0.4.0 or later.")


auditlog = AuditlogModelRegistry()
