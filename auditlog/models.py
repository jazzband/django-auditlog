import ast
import json

from dateutil import parser
from dateutil.tz import gettz
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import DEFAULT_DB_ALIAS, models
from django.db.models import Q, QuerySet
from django.utils import formats, timezone
from django.utils.encoding import smart_str
from django.utils.translation import gettext_lazy as _
from decouple import config
from elasticsearch import AuthenticationException, Elasticsearch

from sary_helpers.request_helpers import get_request_meta

class LogEntryManager(models.Manager):
    """
    Custom manager for the :py:class:`LogEntry` model.
    """

    def log_create(self, instance, **kwargs):
        """
        Helper method to create a new log entry. This method automatically populates some fields when no
        explicit value is given.

        :param instance: The model instance to log a change for.
        :type instance: Model
        :param kwargs: Field overrides for the :py:class:`LogEntry` object.
        :return: The new log entry or `None` if there were no changes.
        :rtype: LogEntry
        """
        changes = kwargs.get("changes", None)
        pk = self._get_pk_value(instance)

        if changes is not None:
            kwargs.setdefault(
                "content_type", ContentType.objects.get_for_model(instance)
            )
            kwargs.setdefault("object_pk", pk)
            kwargs.setdefault("object_repr", smart_str(instance))

            if isinstance(pk, int):
                kwargs.setdefault("object_id", pk)

            get_additional_data = getattr(instance, "get_additional_data", None)
            if callable(get_additional_data):
                kwargs.setdefault("additional_data", get_additional_data())

            # Delete log entries with the same pk as a newly created model.
            # This should only be necessary when an pk is used twice.
            if kwargs.get("action", None) is LogEntry.Action.CREATE:
                if (
                    kwargs.get("object_id", None) is not None
                    and self.filter(
                        content_type=kwargs.get("content_type"),
                        object_id=kwargs.get("object_id"),
                    ).exists()
                ):
                    self.filter(
                        content_type=kwargs.get("content_type"),
                        object_id=kwargs.get("object_id"),
                    ).delete()
                else:
                    self.filter(
                        content_type=kwargs.get("content_type"),
                        object_pk=kwargs.get("object_pk", ""),
                    ).delete()
            log_entry =  self.create(**kwargs)
            self.log_on_elk(log_entry, instance)
            return log_entry
        return None

    def _get_client(self):
        _client = None
        ELASTIC_USER = config("ELASTIC_USER", None)
        ELASTIC_PASSWORD = config("ELASTIC_PASSWORD", None)
        CLOUD_ID = config("CLOUD_ID", None)

        if ELASTIC_USER and ELASTIC_PASSWORD and CLOUD_ID:
            try:
                _client = Elasticsearch(cloud_id=CLOUD_ID, basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD))
                _client.info()
            except AuthenticationException:
                _client = None
        return _client

    def log_on_elk(self, log_entry, instance):
        """
        Logs registed model changes to elasticsearch

        :param instance: The registered model instance.
        :param log_entry: 
        """
        log_actions = {
            0: 'create',
            1: 'update',
            2: 'delete'
        }

        log_doc = {
            'user': log_entry.actor if log_entry.actor else 'system',
            'changes': log_entry.changes,
            'id': log_entry.object_id,
            'action': log_actions[log_entry.action]
        }
        _client = self._get_client()
        _client.index(index=instance._meta.model.__name__.lower() + 'log', document=log_doc)

    def log_m2m_changes(
        self, changed_queryset, instance, operation, field_name, **kwargs
    ):
        """Create a new "changed" log entry from m2m record.

        :param changed_queryset: The added or removed related objects.
        :type changed_queryset: QuerySet
        :param instance: The model instance to log a change for.
        :type instance: Model
        :param operation: "add" or "delete".
        :type action: str
        :param field_name: The name of the changed m2m field.
        :type field_name: str
        :param kwargs: Field overrides for the :py:class:`LogEntry` object.
        :return: The new log entry or `None` if there were no changes.
        :rtype: LogEntry
        """

        pk = self._get_pk_value(instance)
        if changed_queryset is not None:
            kwargs.setdefault(
                "content_type", ContentType.objects.get_for_model(instance)
            )
            kwargs.setdefault("object_pk", pk)
            kwargs.setdefault("object_repr", smart_str(instance))
            kwargs.setdefault("action", LogEntry.Action.UPDATE)

            if isinstance(pk, int):
                kwargs.setdefault("object_id", pk)

            get_additional_data = getattr(instance, "get_additional_data", None)
            if callable(get_additional_data):
                kwargs.setdefault("additional_data", get_additional_data())

            objects = [smart_str(instance) for instance in changed_queryset]
            kwargs["changes"] = json.dumps(
                {
                    field_name: {
                        "type": "m2m",
                        "operation": operation,
                        "objects": objects,
                    }
                }
            )
            return self.create(**kwargs)

        return None

    def get_for_object(self, instance):
        """
        Get log entries for the specified model instance.

        :param instance: The model instance to get log entries for.
        :type instance: Model
        :return: QuerySet of log entries for the given model instance.
        :rtype: QuerySet
        """
        # Return empty queryset if the given model instance is not a model instance.
        if not isinstance(instance, models.Model):
            return self.none()

        content_type = ContentType.objects.get_for_model(instance.__class__)
        pk = self._get_pk_value(instance)

        if isinstance(pk, int):
            return self.filter(content_type=content_type, object_id=pk)
        else:
            return self.filter(content_type=content_type, object_pk=smart_str(pk))

    def get_for_objects(self, queryset):
        """
        Get log entries for the objects in the specified queryset.

        :param queryset: The queryset to get the log entries for.
        :type queryset: QuerySet
        :return: The LogEntry objects for the objects in the given queryset.
        :rtype: QuerySet
        """
        if not isinstance(queryset, QuerySet) or queryset.count() == 0:
            return self.none()

        content_type = ContentType.objects.get_for_model(queryset.model)
        primary_keys = list(
            queryset.values_list(queryset.model._meta.pk.name, flat=True)
        )

        if isinstance(primary_keys[0], int):
            return (
                self.filter(content_type=content_type)
                .filter(Q(object_id__in=primary_keys))
                .distinct()
            )
        elif isinstance(queryset.model._meta.pk, models.UUIDField):
            primary_keys = [smart_str(pk) for pk in primary_keys]
            return (
                self.filter(content_type=content_type)
                .filter(Q(object_pk__in=primary_keys))
                .distinct()
            )
        else:
            return (
                self.filter(content_type=content_type)
                .filter(Q(object_pk__in=primary_keys))
                .distinct()
            )

    def get_for_model(self, model):
        """
        Get log entries for all objects of a specified type.

        :param model: The model to get log entries for.
        :type model: class
        :return: QuerySet of log entries for the given model.
        :rtype: QuerySet
        """
        # Return empty queryset if the given object is not valid.
        if not issubclass(model, models.Model):
            return self.none()

        content_type = ContentType.objects.get_for_model(model)

        return self.filter(content_type=content_type)

    def _get_pk_value(self, instance):
        """
        Get the primary key field value for a model instance.

        :param instance: The model instance to get the primary key for.
        :type instance: Model
        :return: The primary key value of the given model instance.
        """
        pk_field = instance._meta.pk.name
        pk = getattr(instance, pk_field, None)

        # Check to make sure that we got an pk not a model object.
        if isinstance(pk, models.Model):
            pk = self._get_pk_value(pk)
        return pk


class LogEntry(models.Model):
    """
    Represents an entry in the audit log. The content type is saved along with the textual and numeric
    (if available) primary key, as well as the textual representation of the object when it was saved.
    It holds the action performed and the fields that were changed in the transaction.

    If AuditlogMiddleware is used, the actor will be set automatically. Keep in mind that
    editing / re-saving LogEntry instances may set the actor to a wrong value - editing LogEntry
    instances is not recommended (and it should not be necessary).
    """

    class Action:
        """
        The actions that Auditlog distinguishes: creating, updating and deleting objects. Viewing objects
        is not logged. The values of the actions are numeric, a higher integer value means a more intrusive
        action. This may be useful in some cases when comparing actions because the ``__lt``, ``__lte``,
        ``__gt``, ``__gte`` lookup filters can be used in queries.

        The valid actions are :py:attr:`Action.CREATE`, :py:attr:`Action.UPDATE` and :py:attr:`Action.DELETE`.
        """

        CREATE = 0
        UPDATE = 1
        DELETE = 2

        choices = (
            (CREATE, _("create")),
            (UPDATE, _("update")),
            (DELETE, _("delete")),
        )

    content_type = models.ForeignKey(
        to="contenttypes.ContentType",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("content type"),
    )
    object_pk = models.CharField(
        db_index=True, max_length=255, verbose_name=_("object pk")
    )
    object_id = models.BigIntegerField(
        blank=True, db_index=True, null=True, verbose_name=_("object id")
    )
    object_repr = models.TextField(verbose_name=_("object representation"))
    action = models.PositiveSmallIntegerField(
        choices=Action.choices, verbose_name=_("action"), db_index=True
    )
    changes = models.TextField(blank=True, verbose_name=_("change message"))
    actor = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name=_("actor"),
    )
    remote_addr = models.GenericIPAddressField(
        blank=True, null=True, verbose_name=_("remote address")
    )
    timestamp = models.DateTimeField(
        db_index=True, auto_now_add=True, verbose_name=_("timestamp")
    )
    additional_data = models.JSONField(
        blank=True, null=True, verbose_name=_("additional data")
    )

    objects = LogEntryManager()

    class Meta:
        get_latest_by = "timestamp"
        ordering = ["-timestamp"]
        verbose_name = _("log entry")
        verbose_name_plural = _("log entries")

    def __str__(self):
        if self.action == self.Action.CREATE:
            fstring = _("Created {repr:s}")
        elif self.action == self.Action.UPDATE:
            fstring = _("Updated {repr:s}")
        elif self.action == self.Action.DELETE:
            fstring = _("Deleted {repr:s}")
        else:
            fstring = _("Logged {repr:s}")

        return fstring.format(repr=self.object_repr)

    @property
    def changes_dict(self):
        """
        :return: The changes recorded in this log entry as a dictionary object.
        """
        try:
            return json.loads(self.changes)
        except ValueError:
            return {}

    @property
    def changes_str(self, colon=": ", arrow=" \u2192 ", separator="; "):
        """
        Return the changes recorded in this log entry as a string. The formatting of the string can be
        customized by setting alternate values for colon, arrow and separator. If the formatting is still
        not satisfying, please use :py:func:`LogEntry.changes_dict` and format the string yourself.

        :param colon: The string to place between the field name and the values.
        :param arrow: The string to place between each old and new value.
        :param separator: The string to place between each field.
        :return: A readable string of the changes in this log entry.
        """
        substrings = []

        for field, values in self.changes_dict.items():
            substring = "{field_name:s}{colon:s}{old:s}{arrow:s}{new:s}".format(
                field_name=field,
                colon=colon,
                old=values[0],
                arrow=arrow,
                new=values[1],
            )
            substrings.append(substring)

        return separator.join(substrings)

    @property
    def changes_display_dict(self):
        """
        :return: The changes recorded in this log entry intended for display to users as a dictionary object.
        """
        # Get the model and model_fields
        from auditlog.registry import auditlog

        model = self.content_type.model_class()
        model_fields = auditlog.get_model_fields(model._meta.model)
        changes_display_dict = {}
        # grab the changes_dict and iterate through
        for field_name, values in self.changes_dict.items():
            # try to get the field attribute on the model
            try:
                field = model._meta.get_field(field_name)
            except FieldDoesNotExist:
                changes_display_dict[field_name] = values
                continue
            values_display = []
            # handle choices fields and Postgres ArrayField to get human readable version
            choices_dict = None
            if getattr(field, "choices", []):
                choices_dict = dict(field.choices)
            if getattr(getattr(field, "base_field", None), "choices", []):
                choices_dict = dict(field.base_field.choices)

            if choices_dict:
                for value in values:
                    try:
                        value = ast.literal_eval(value)
                        if type(value) is [].__class__:
                            values_display.append(
                                ", ".join(
                                    [choices_dict.get(val, "None") for val in value]
                                )
                            )
                        else:
                            values_display.append(choices_dict.get(value, "None"))
                    except Exception:
                        values_display.append(choices_dict.get(value, "None"))
            else:
                try:
                    field_type = field.get_internal_type()
                except AttributeError:
                    # if the field is a relationship it has no internal type and exclude it
                    continue
                for value in values:
                    # handle case where field is a datetime, date, or time type
                    if field_type in ["DateTimeField", "DateField", "TimeField"]:
                        try:
                            value = parser.parse(value)
                            if field_type == "DateField":
                                value = value.date()
                            elif field_type == "TimeField":
                                value = value.time()
                            elif field_type == "DateTimeField":
                                value = value.replace(tzinfo=timezone.utc)
                                value = value.astimezone(gettz(settings.TIME_ZONE))
                            value = formats.localize(value)
                        except ValueError:
                            pass
                    # check if length is longer than 140 and truncate with ellipsis
                    if len(value) > 140:
                        value = f"{value[:140]}..."

                    values_display.append(value)
            verbose_name = model_fields["mapping_fields"].get(
                field.name, getattr(field, "verbose_name", field.name)
            )
            changes_display_dict[verbose_name] = values_display
        return changes_display_dict


class AuditlogHistoryField(GenericRelation):
    """
    A subclass of py:class:`django.contrib.contenttypes.fields.GenericRelation` that sets some default
    variables. This makes it easier to access Auditlog's log entries, for example in templates.

    By default this field will assume that your primary keys are numeric, simply because this is the most
    common case. However, if you have a non-integer primary key, you can simply pass ``pk_indexable=False``
    to the constructor, and Auditlog will fall back to using a non-indexed text based field for this model.

    Using this field will not automatically register the model for automatic logging. This is done so you
    can be more flexible with how you use this field.

    :param pk_indexable: Whether the primary key for this model is not an :py:class:`int` or :py:class:`long`.
    :type pk_indexable: bool
    :param delete_related: By default, including a generic relation into a model will cause all related
        objects to be cascade-deleted when the parent object is deleted. Passing False to this overrides this
        behavior, retaining the full auditlog history for the object. Defaults to True, because that's
        Django's default behavior.
    :type delete_related: bool
    """

    def __init__(self, pk_indexable=True, delete_related=True, **kwargs):
        kwargs["to"] = LogEntry

        if pk_indexable:
            kwargs["object_id_field"] = "object_id"
        else:
            kwargs["object_id_field"] = "object_pk"

        kwargs["content_type_field"] = "content_type"
        self.delete_related = delete_related
        super().__init__(**kwargs)

    def bulk_related_objects(self, objs, using=DEFAULT_DB_ALIAS):
        """
        Return all objects related to ``objs`` via this ``GenericRelation``.
        """
        if self.delete_related:
            return super().bulk_related_objects(objs, using)

        # When deleting, Collector.collect() finds related objects using this
        # method.  However, because we don't want to delete these related
        # objects, we simply return an empty list.
        return []
