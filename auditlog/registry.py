from typing import Dict, Callable, Optional, List, Tuple

from django.db.models import Model
from django.db.models.base import ModelBase
from django.db.models.signals import pre_save, post_save, post_delete, ModelSignal

DispatchUID = Tuple[int, str, int]


class AuditlogModelRegistry(object):
    """
    A registry that keeps track of the models that use Auditlog to track changes.
    """

    def __init__(self, create: bool = True, update: bool = True, delete: bool = True,
                 custom: Optional[Dict[ModelSignal, Callable]] = None):
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

    def register(self, model: ModelBase = None, include_fields: Optional[List[str]] = None,
                 exclude_fields: Optional[List[str]] = None, mapping_fields: Optional[Dict[str, str]] = None):
        """
        Register a model with auditlog. Auditlog will then track mutations on this model's instances.

        :param model: The model to register.
        :param include_fields: The fields to include. Implicitly excludes all other fields.
        :param exclude_fields: The fields to exclude. Overrides the fields to include.
        :param mapping_fields: Mapping from field names to strings in diff.

        """

        if include_fields is None:
            include_fields = []
        if exclude_fields is None:
            exclude_fields = []
        if mapping_fields is None:
            mapping_fields = {}

        def registrar(cls):
            """Register models for a given class."""
            if not issubclass(cls, Model):
                raise TypeError("Supplied model is not a valid model.")

            self._registry[cls] = {
                'include_fields': include_fields,
                'exclude_fields': exclude_fields,
                'mapping_fields': mapping_fields,
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

    def contains(self, model: ModelBase) -> bool:
        """
        Check if a model is registered with auditlog.

        :param model: The model to check.
        :return: Whether the model has been registered.
        :rtype: bool
        """
        return model in self._registry

    def unregister(self, model: ModelBase) -> None:
        """
        Unregister a model with auditlog. This will not affect the database.

        :param model: The model to unregister.
        """
        try:
            del self._registry[model]
        except KeyError:
            pass
        else:
            self._disconnect_signals(model)

    def get_models(self) -> List[ModelBase]:
        return list(self._registry.keys())

    def get_model_fields(self, model: ModelBase):
        return {
            'include_fields': list(self._registry[model]['include_fields']),
            'exclude_fields': list(self._registry[model]['exclude_fields']),
            'mapping_fields': dict(self._registry[model]['mapping_fields']),
        }

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
        for signal, receiver in self._signals.items():
            signal.disconnect(sender=model, dispatch_uid=self._dispatch_uid(signal, model))

    def _dispatch_uid(self, signal, model) -> DispatchUID:
        """
        Generate a dispatch_uid.
        """
        return self.__hash__(), model.__qualname__, signal.__hash__()


auditlog = AuditlogModelRegistry()
