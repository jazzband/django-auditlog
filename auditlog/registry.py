import copy
from collections import defaultdict
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
)

from django.apps import apps
from django.db.models import Model
from django.db.models.base import ModelBase
from django.db.models.signals import (
    ModelSignal,
    m2m_changed,
    post_delete,
    post_save,
    pre_save,
)

from auditlog.conf import settings
from auditlog.signals import accessed

DispatchUID = Tuple[int, int, int]


class AuditLogRegistrationError(Exception):
    pass


class AuditlogModelRegistry:
    """
    A registry that keeps track of the models that use Auditlog to track changes.
    """

    DEFAULT_EXCLUDE_MODELS = ("auditlog.LogEntry", "admin.LogEntry")

    def __init__(
        self,
        create: bool = True,
        update: bool = True,
        delete: bool = True,
        access: bool = True,
        m2m: bool = True,
        custom: Optional[Dict[ModelSignal, Callable]] = None,
    ):
        from auditlog.receivers import log_access, log_create, log_delete, log_update

        self._registry = {}
        self._signals = {}
        self._m2m_signals = defaultdict(dict)

        if create:
            self._signals[post_save] = log_create
        if update:
            self._signals[pre_save] = log_update
        if delete:
            self._signals[post_delete] = log_delete
        if access:
            self._signals[accessed] = log_access
        self._m2m = m2m

        if custom is not None:
            self._signals.update(custom)

    def register(
        self,
        model: ModelBase = None,
        include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None,
        mapping_fields: Optional[Dict[str, str]] = None,
        mask_fields: Optional[List[str]] = None,
        m2m_fields: Optional[Collection[str]] = None,
        serialize_data: bool = False,
        serialize_kwargs: Optional[Dict[str, Any]] = None,
        serialize_auditlog_fields_only: bool = False,
    ):
        """
        Register a model with auditlog. Auditlog will then track mutations on this model's instances.

        :param model: The model to register.
        :param include_fields: The fields to include. Implicitly excludes all other fields.
        :param exclude_fields: The fields to exclude. Overrides the fields to include.
        :param mapping_fields: Mapping from field names to strings in diff.
        :param mask_fields: The fields to mask for sensitive info.
        :param m2m_fields: The fields to handle as many to many.
        :param serialize_data: Option to include a dictionary of the objects state in the auditlog.
        :param serialize_kwargs: Optional kwargs to pass to Django serializer
        :param serialize_auditlog_fields_only: Only fields being considered in changes will be serialized.
        """

        if include_fields is None:
            include_fields = []
        if exclude_fields is None:
            exclude_fields = []
        if mapping_fields is None:
            mapping_fields = {}
        if mask_fields is None:
            mask_fields = []
        if m2m_fields is None:
            m2m_fields = set()
        if serialize_kwargs is None:
            serialize_kwargs = {}

        if (serialize_kwargs or serialize_auditlog_fields_only) and not serialize_data:
            raise AuditLogRegistrationError(
                "Serializer options were given but the 'serialize_data' option is not "
                "set. Did you forget to set serialized_data to True?"
            )

        def registrar(cls):
            """Register models for a given class."""
            if not issubclass(cls, Model):
                raise TypeError("Supplied model is not a valid model.")

            self._registry[cls] = {
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "mapping_fields": mapping_fields,
                "mask_fields": mask_fields,
                "m2m_fields": m2m_fields,
                "serialize_data": serialize_data,
                "serialize_kwargs": serialize_kwargs,
                "serialize_auditlog_fields_only": serialize_auditlog_fields_only,
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

    def get_serialize_options(self, model: ModelBase):
        return {
            "serialize_data": bool(self._registry[model]["serialize_data"]),
            "serialize_kwargs": dict(self._registry[model]["serialize_kwargs"]),
            "serialize_auditlog_fields_only": bool(
                self._registry[model]["serialize_auditlog_fields_only"]
            ),
        }

    def _connect_signals(self, model):
        """
        Connect signals for the model.
        """
        from auditlog.receivers import make_log_m2m_changes

        for signal, receiver in self._signals.items():
            signal.connect(
                receiver,
                sender=model,
                dispatch_uid=self._dispatch_uid(signal, receiver),
            )
        if self._m2m:
            for field_name in self._registry[model]["m2m_fields"]:
                receiver = make_log_m2m_changes(field_name)
                self._m2m_signals[model][field_name] = receiver
                field = getattr(model, field_name)
                m2m_model = getattr(field, "through")

                m2m_changed.connect(
                    receiver,
                    sender=m2m_model,
                    dispatch_uid=self._dispatch_uid(m2m_changed, receiver),
                )

    def _disconnect_signals(self, model):
        """
        Disconnect signals for the model.
        """
        for signal, receiver in self._signals.items():
            signal.disconnect(
                sender=model, dispatch_uid=self._dispatch_uid(signal, receiver)
            )
        for field_name, receiver in self._m2m_signals[model].items():
            field = getattr(model, field_name)
            m2m_model = getattr(field, "through")
            m2m_changed.disconnect(
                sender=m2m_model,
                dispatch_uid=self._dispatch_uid(m2m_changed, receiver),
            )
        del self._m2m_signals[model]

    def _dispatch_uid(self, signal, receiver) -> DispatchUID:
        """Generate a dispatch_uid which is unique for a combination of self, signal, and receiver."""
        return id(self), id(signal), id(receiver)

    def _get_model_classes(self, app_model: str) -> List[ModelBase]:
        try:
            try:
                app_label, model_name = app_model.split(".")
                return [apps.get_model(app_label, model_name)]
            except ValueError:
                return apps.get_app_config(app_model).get_models()
        except LookupError:
            return []

    def _get_exclude_models(
        self, exclude_tracking_models: Iterable[str]
    ) -> List[ModelBase]:
        exclude_models = [
            model
            for app_model in exclude_tracking_models + self.DEFAULT_EXCLUDE_MODELS
            for model in self._get_model_classes(app_model)
        ]
        return exclude_models

    def _register_models(self, models: Iterable[Union[str, Dict[str, Any]]]) -> None:
        models = copy.deepcopy(models)
        for model in models:
            if isinstance(model, str):
                for model_class in self._get_model_classes(model):
                    self.unregister(model_class)
                    self.register(model_class)
            elif isinstance(model, dict):
                model["model"] = self._get_model_classes(model["model"])[0]
                self.unregister(model["model"])
                self.register(**model)

    def register_from_settings(self):
        """
        Register models from settings variables
        """
        if not isinstance(settings.AUDITLOG_INCLUDE_ALL_MODELS, bool):
            raise TypeError("Setting 'AUDITLOG_INCLUDE_ALL_MODELS' must be a boolean")
        if not isinstance(settings.AUDITLOG_DISABLE_ON_RAW_SAVE, bool):
            raise TypeError("Setting 'AUDITLOG_DISABLE_ON_RAW_SAVE' must be a boolean")
        if not isinstance(settings.AUDITLOG_EXCLUDE_TRACKING_MODELS, (list, tuple)):
            raise TypeError(
                "Setting 'AUDITLOG_EXCLUDE_TRACKING_MODELS' must be a list or tuple"
            )

        if (
            not settings.AUDITLOG_INCLUDE_ALL_MODELS
            and settings.AUDITLOG_EXCLUDE_TRACKING_MODELS
        ):
            raise ValueError(
                "In order to use setting 'AUDITLOG_EXCLUDE_TRACKING_MODELS', "
                "setting 'AUDITLOG_INCLUDE_ALL_MODELS' must set to 'True'"
            )

        if not isinstance(settings.AUDITLOG_INCLUDE_TRACKING_MODELS, (list, tuple)):
            raise TypeError(
                "Setting 'AUDITLOG_INCLUDE_TRACKING_MODELS' must be a list or tuple"
            )

        for item in settings.AUDITLOG_INCLUDE_TRACKING_MODELS:
            if not isinstance(item, (str, dict)):
                raise TypeError(
                    "Setting 'AUDITLOG_INCLUDE_TRACKING_MODELS' items must be str or dict"
                )

            if isinstance(item, dict):
                if "model" not in item:
                    raise ValueError(
                        "Setting 'AUDITLOG_INCLUDE_TRACKING_MODELS' dict items must contain 'model' key"
                    )
                if "." not in item["model"]:
                    raise ValueError(
                        "Setting 'AUDITLOG_INCLUDE_TRACKING_MODELS' model must be in the "
                        "format <app_name>.<model_name>"
                    )

        if settings.AUDITLOG_INCLUDE_ALL_MODELS:
            exclude_models = self._get_exclude_models(
                settings.AUDITLOG_EXCLUDE_TRACKING_MODELS
            )
            models = apps.get_models()

            for model in models:
                if model in exclude_models:
                    continue
                self.register(model)

        self._register_models(settings.AUDITLOG_INCLUDE_TRACKING_MODELS)


auditlog = AuditlogModelRegistry()
