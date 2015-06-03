from __future__ import unicode_literals

import json
import threading

from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible, smart_text
from django.utils.six import iteritems, integer_types
from django.utils.translation import ugettext_lazy as _


class LogEntryManager(models.Manager):
    """
    Custom manager for the LogEntry model.
    """

    def log_create(self, instance, **kwargs):
        """
        Helper method to create a new log entry. This method automatically fills in some data when it is left out. It
        was created to keep things DRY.
        """
        changes = kwargs.get('changes', None)
        pk = self._get_pk_value(instance)

        if changes is not None:
            kwargs.setdefault('content_type', ContentType.objects.get_for_model(instance))
            kwargs.setdefault('object_pk', pk)
            kwargs.setdefault('object_repr', smart_text(instance))

            if isinstance(pk, integer_types):
                kwargs.setdefault('object_id', pk)

            # Delete log entries with the same pk as a newly created model. This should only be necessary when an pk is
            # used twice.
            if kwargs.get('action', None) is LogEntry.Action.CREATE:
                if kwargs.get('object_id', None) is not None and self.filter(content_type=kwargs.get('content_type'), object_id=kwargs.get('object_id')).exists():
                    self.filter(content_type=kwargs.get('content_type'), object_id=kwargs.get('object_id')).delete()
                else:
                    self.filter(content_type=kwargs.get('content_type'), object_pk=kwargs.get('object_pk', '')).delete()

            return self.create(**kwargs)
        return None

    def get_for_object(self, instance):
        """
        Get log entries for the specified model instance.
        """
        # Return empty queryset if the given model instance is not a model instance.
        if not isinstance(instance, models.Model):
            return self.none()

        content_type = ContentType.objects.get_for_model(instance.__class__)
        pk = self._get_pk_value(instance)

        if isinstance(pk, integer_types):
            return self.filter(content_type=content_type, object_id=pk)
        else:
            return self.filter(content_type=content_type, object_pk=pk)

    def get_for_model(self, model):
        """
        Get log entries for all objects of a specified type.
        """
        # Return empty queryset if the given object is not valid.
        if not issubclass(model, models.Model):
            return self.none()

        content_type = ContentType.objects.get_for_model(model)

        return self.filter(content_type=content_type)

    def _get_pk_value(self, instance):
        """
        Get the primary key field value for a model instance.
        """
        pk_field = instance._meta.pk.name
        pk = getattr(instance, pk_field, None)

        # Check to make sure that we got an pk not a model object.
        if isinstance(pk, models.Model):
            pk = self._get_pk_value(pk)
        return pk


@python_2_unicode_compatible
class LogEntry(models.Model):
    """
    Represents an entry in the audit log. The content type is saved along with the textual and numeric (if available)
    primary key, as well as the textual representation of the object when it was saved. It holds the action performed
    and the fields that were changed in the transaction.

    If AuditlogMiddleware is used, the actor will be set automatically. Keep in mind that editing / re-saving LogEntry
    instances may set the actor to a wrong value - editing LogEntry instances is not recommended (and it should not be
    necessary).
    """

    class Action:
        """
        The actions that Auditlog distinguishes: creating, updating and deleting objects. Viewing objects is not logged.
        The values of the actions are numeric, a higher integer value means a more intrusive action. This may be useful
        in some cases when comparing actions because __lt, __lte, __gt, __gte can be used in queries.
        """
        CREATE = 0
        UPDATE = 1
        DELETE = 2

        choices = (
            (CREATE, _("create")),
            (UPDATE, _("update")),
            (DELETE, _("delete")),
        )

    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE, related_name='+', verbose_name=_("content type"))
    object_pk = models.TextField(verbose_name=_("object pk"))
    object_id = models.BigIntegerField(blank=True, db_index=True, null=True, verbose_name=_("object id"))
    object_repr = models.TextField(verbose_name=_("object representation"))
    action = models.PositiveSmallIntegerField(choices=Action.choices, verbose_name=_("action"))
    changes = models.TextField(blank=True, verbose_name=_("change message"))
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL, related_name='+', verbose_name=_("actor"))
    remote_addr = models.GenericIPAddressField(blank=True, null=True, verbose_name=_("remote address"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("timestamp"))

    objects = LogEntryManager()

    class Meta:
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']
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

    def clean(self):
        threadlocal = threading.local()

        # Set remote_addr on creation if empty and available in thread
        if not self.pk and self.remote_addr is None and hasattr(threadlocal, 'auditlog'):
            self.remote_addr = threading.local().auditlog.get('remote_addr', None)

    @property
    def changes_dict(self):
        """
        Return the changes recorded in this log entry as a dictionary object.
        """
        try:
            return json.loads(self.changes)
        except ValueError:
            return {}

    @property
    def changes_str(self, colon=': ', arrow=smart_text(' \u2192 '), separator='; '):
        """
        Return the changes recorded in this log entry as a string. The formatting of the string can be customized by
        setting alternate values for colon, arrow and separator. If the formatting is still not satisfying, please use
        changes_dict() and format the string yourself.
        """
        substrings = []

        for field, values in iteritems(self.changes_dict):
            substring = smart_text('{field_name:s}{colon:s}{old:s}{arrow:s}{new:s}').format(
                field_name=field,
                colon=colon,
                old=values[0],
                arrow=arrow,
                new=values[1],
            )
            substrings.append(substring)

        return separator.join(substrings)


class AuditlogHistoryField(generic.GenericRelation):
    """
    A subclass of django.contrib.contenttypes.generic.GenericRelation that sets some default variables. This makes it
    easier to implement the audit log in models, and makes future changes easier.

    By default this field will assume that your primary keys are numeric, simply because this is the most common case.
    However, if you have a non-integer primary key, you can simply pass pk_indexable=False to the constructor, and
    Auditlog will fall back to using a non-indexed text based field for this model.

    Using this field will not automatically register the model for automatic logging. This is done so you can be more
    flexible with how you use this field.
    """

    def __init__(self, pk_indexable=True, **kwargs):
        kwargs['to'] = LogEntry

        if pk_indexable:
            kwargs['object_id_field'] = 'object_id'
        else:
            kwargs['object_id_field'] = 'object_pk'

        kwargs['content_type_field'] = 'content_type'
        super(AuditlogHistoryField, self).__init__(**kwargs)

# South compatibility for AuditlogHistoryField
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^auditlog\.models\.AuditlogHistoryField"])
    raise DeprecationWarning("South support will be dropped in django-auditlog 0.4.0 or later.")
except ImportError:
    pass
