import copy
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

from django.apps import apps
from django.conf import settings
from django.db.models import Model
from django.db.models.base import ModelBase
from django.db.models.signals import ModelSignal, post_delete, post_save, pre_save

DispatchUID = Tuple[int, str, int]


_DEFAULT_EXCLUDE_MODELS = ("auditlog.LogEntry", "admin.LogEntry")


class AuditlogModelRegistry:
    """
    A registry that keeps track of the models that use Auditlog to track changes.
    """

    def __init__(
        self,
        create: bool = True,
        update: bool = True,
        delete: bool = True,
        custom: Optional[Dict[ModelSignal, Callable]] = None,
    ):
        from auditlog.receivers import log_create, log_delete, log_update

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

    def register(
        self,
        model: ModelBase = None,
        include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None,
        mapping_fields: Optional[Dict[str, str]] = None,
        mask_fields: Optional[List[str]] = None,
    ):
        """
        Register a model with auditlog. Auditlog will then track mutations on this model's instances.

        :param model: The model to register.
        :param include_fields: The fields to include. Implicitly excludes all other fields.
        :param exclude_fields: The fields to exclude. Overrides the fields to include.
        :param mapping_fields: Mapping from field names to strings in diff.
        :param mask_fields: The fields to mask for sensitive info.

        """

        if include_fields is None:
            include_fields = []
        if exclude_fields is None:
            exclude_fields = []
        if mapping_fields is None:
            mapping_fields = {}
        if mask_fields is None:
            mask_fields = []

        def registrar(cls):
            """Register models for a given class."""
            if not issubclass(cls, Model):
                raise TypeError("Supplied model is not a valid model.")

            self._registry[cls] = {
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "mapping_fields": mapping_fields,
                "mask_fields": mask_fields,
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
            "include_fields": list(self._registry[model]["include_fields"]),
            "exclude_fields": list(self._registry[model]["exclude_fields"]),
            "mapping_fields": dict(self._registry[model]["mapping_fields"]),
            "mask_fields": list(self._registry[model]["mask_fields"]),
        }

    def _connect_signals(self, model):
        """
        Connect signals for the model.
        """
        for signal in self._signals:
            receiver = self._signals[signal]
            signal.connect(
                receiver, sender=model, dispatch_uid=self._dispatch_uid(signal, model)
            )

    def _disconnect_signals(self, model):
        """
        Disconnect signals for the model.
        """
        for signal, receiver in self._signals.items():
            signal.disconnect(
                sender=model, dispatch_uid=self._dispatch_uid(signal, model)
            )

    def _dispatch_uid(self, signal, model) -> DispatchUID:
        """
        Generate a dispatch_uid.
        """
        return self.__hash__(), model.__qualname__, signal.__hash__()


def _get_model_classes(app_model: str) -> List[ModelBase]:
    try:
        try:
            app_label, model_name = app_model.split(".")
            return [apps.get_model(app_label, model_name)]
        except ValueError:
            return apps.get_app_config(app_model).get_models()
    except LookupError:
        return []


def _auditlog_register_models(
    auditlog: AuditlogModelRegistry, models: Iterable[Union[str, Dict[str, Any]]]
):
    models = copy.deepcopy(models)

    if not isinstance(models, list) and not isinstance(models, tuple):
        raise TypeError(f"'models'({type(models)}) is not an list or tuple")

    for model in models:
        if isinstance(model, str):
            for model_class in _get_model_classes(model):
                auditlog.unregister(model_class)
                auditlog.register(model_class)

        elif isinstance(model, dict):
            if "model" not in model:
                raise ValueError("item must contain 'model' key")
            if "." not in model["model"]:
                raise ValueError(
                    "model with options must be in the format <app_name>.<model_name>"
                )
            try:
                model["model"] = _get_model_classes(model["model"])[0]
                auditlog.unregister(model["model"])
                auditlog.register(**model)
            except IndexError:
                pass
        else:
            raise TypeError("item must be a dict or str")


def get_exclude_models():
    exclude_models: List[ModelBase] = [
        model
        for app_model in getattr(settings, "AUDITLOG_EXCLUDE_TRACKING_MODELS", ())
        + _DEFAULT_EXCLUDE_MODELS
        for model in _get_model_classes(app_model)
    ]
    return exclude_models


def auditlog_register(
    auditlog: AuditlogModelRegistry,
    include_all_models=False,
    include_auto_created=False,
):
    if getattr(settings, "AUDITLOG_INCLUDE_ALL_MODELS", False) or include_all_models:
        exclude_models = get_exclude_models()
        models = apps.get_models(include_auto_created=include_auto_created)

        for model in models:
            if model in exclude_models:
                continue
            auditlog.register(model)

    _auditlog_register_models(
        auditlog, getattr(settings, "AUDITLOG_INCLUDE_TRACKING_MODELS", ())
    )


auditlog = AuditlogModelRegistry()
