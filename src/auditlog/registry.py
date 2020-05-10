from __future__ import unicode_literals

from django.db.models.signals import pre_save, post_save, post_delete, m2m_changed
from django.db.models import Model
from django.utils.six import iteritems


class AuditlogModelRegistry(object):
    """
    A registry that keeps track of the models that use Auditlog to track changes.
    """
    def __init__(self, create=True, update=True, delete=True, m2m=True, custom=None):
        from auditlog.receivers import log_create, log_update, log_delete, log_m2m_changes

        self._registry = {}
        self._signals = {}

        if create:
            self._signals[post_save] = log_create
        if update:
            self._signals[pre_save] = log_update
        if delete:
            self._signals[post_delete] = log_delete
        if m2m:
            self._signals[m2m_changed] = log_m2m_changes

        if custom is not None:
            self._signals.update(custom)

    def register(self, model=None, include_fields=[], exclude_fields=[], mapping_fields={}, m2m_fields={}):
        """
        Register a model with auditlog. Auditlog will then track mutations on this model's instances.

        :param model: The model to register.
        :type model: Model
        :param include_fields: The fields to include. Implicitly excludes all other fields.
        :type include_fields: list
        :param exclude_fields: The fields to exclude. Overrides the fields to include.
        :type exclude_fields: list
        :param m2m_fields: The fields to map as many to many.
        :type m2m_fields: dict of key: list pairs

        """
        def registrar(cls):
            """Register models for a given class."""
            if not issubclass(cls, Model):
                raise TypeError("Supplied model is not a valid model.")

            self._registry[cls] = {
                'include_fields': include_fields,
                'exclude_fields': exclude_fields,
                'mapping_fields': mapping_fields,
                'm2m_fields': m2m_fields
            }
            self._connect_signals(cls)

            # We need to return the class, as the decorator is basically
            # syntactic sugar for:
            # MyClass = auditlog.register(MyClass)
            return cls

        if model is None:
            # If we're being used as a decorator, return a callable with the
            # wrapper.
            return lambda cls: registrar(cls)
        else:
            # Otherwise, just register the model.
            registrar(model)

    def contains(self, model):
        """
        Check if a model is registered with auditlog.

        :param model: The model to check.
        :type model: Model
        :return: Whether the model has been registered.
        :rtype: bool
        """
        return model in self._registry

    def unregister(self, model):
        """
        Unregister a model with auditlog. This will not affect the database.

        :param model: The model to unregister.
        :type model: Model
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

            if signal is m2m_changed:
                # Connect Many to many signals
                for m2m_field, m2m_signals in self._registry[model]['m2m_fields'].items():
                    assert isinstance(m2m_signals, list)
                    if m2m_signals == []:
                        m2m_signals = 'post_add', 'post_remove', 'post_clear'

                    field = getattr(model, m2m_field)
                    m2m_model = getattr(field, 'through')
                    if 'post_save' in m2m_signals:
                        post_save_receiver = self._signals[post_save]
                        post_save.connect(post_save_receiver, sender=m2m_model, dispatch_uid=self._dispatch_uid(m2m_model, model))

                    if 'pre_save' in m2m_signals:
                        pre_save_receiver = self._signals[pre_save]
                        pre_save.connect(pre_save_receiver, sender=m2m_model, dispatch_uid=self._dispatch_uid(m2m_model, model))

                    setattr(m2m_model, '_map_signals', m2m_signals)
                    signal.connect(receiver, sender=m2m_model, dispatch_uid=self._dispatch_uid(signal, m2m_model))
            else:
                signal.connect(receiver, sender=model, dispatch_uid=self._dispatch_uid(signal, model))

    def _disconnect_signals(self, model):
        """
        Disconnect signals for the model.
        """
        for signal, receiver in self._signals.items():
            signal.disconnect(sender=model, dispatch_uid=self._dispatch_uid(signal, model))

    def _dispatch_uid(self, signal, model):
        """
        Generate a dispatch_uid.
        """
        return (self.__class__, model, signal)

    def get_model_fields(self, model):
        return {
            'include_fields': self._registry[model]['include_fields'],
            'exclude_fields': self._registry[model]['exclude_fields'],
            'mapping_fields': self._registry[model]['mapping_fields'],
        }


class AuditLogModelRegistry(AuditlogModelRegistry):
    def __init__(self, *args, **kwargs):
        super(AuditLogModelRegistry, self).__init__(*args, **kwargs)
        raise DeprecationWarning("Use AuditlogModelRegistry instead of AuditLogModelRegistry, AuditLogModelRegistry will be removed in django-auditlog 0.4.0 or later.")


auditlog = AuditlogModelRegistry()
