from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
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

        if changes is not None:
            if not 'content_type' in kwargs:
                kwargs['content_type'] = ContentType.objects.get_for_model(instance)
            if not 'object_pk' in kwargs:
                kwargs['object_pk'] = instance.pk
            if not 'object_repr' in kwargs:
                kwargs['object_repr'] = str(instance)
            if not 'object_id' in kwargs:
                pk_field = instance._meta.pk.name
                pk = getattr(instance, pk_field, None)
                if isinstance(pk, int):
                    kwargs['object_id'] = pk

            # Delete log entries with the same pk as a newly created model. This should only happen when all records were
            # deleted / the table was truncated.
            if kwargs.get('action', None) is LogEntry.Action.CREATE:
                if kwargs.get('object_id', None) is not None and self.filter(content_type=kwargs.get('content_type'), object_id=kwargs.get('object_id')).exists():
                    self.filter(content_type=kwargs.get('content_type'), object_id=kwargs.get('object_id')).delete()
                else:
                    self.filter(content_type=kwargs.get('content_type'), object_pk=kwargs.get('object_pk', '')).delete()

            return self.create(**kwargs)
        return None


class LogEntry(models.Model):
    """
    Represents an entry in the audit log, containing data.
    """

    class Action:
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
    object_id = models.PositiveIntegerField(blank=True, db_index=True, null=True, verbose_name=_("object id"))
    object_repr = models.TextField(verbose_name=_("object representation"))
    action = models.PositiveSmallIntegerField(choices=Action.choices, verbose_name=_("action"))
    changes = models.TextField(blank=True, verbose_name=_("change message"))
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL, related_name='+', verbose_name=_("actor"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("timestamp"))

    objects = LogEntryManager()

    class Meta:
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']
        verbose_name = _("log entry")
        verbose_name_plural = _("log entries")

    def __unicode__(self):
        if self.action == self.Action.CREATE:
            fstring = _("Created {repr:s}")
        elif self.action == self.Action.UPDATE:
            fstring = _("Updated {repr:s}")
        elif self.action == self.Action.DELETE:
            fstring = _("Deleted {repr:s}")
        else:
            fstring = _("Logged {repr:s}")

        return fstring.format(repr=self.object_repr)


class AuditLogHistoryField(generic.GenericRelation):
    """
    A subclass of django.contrib.contenttypes.generic.GenericRelation that sets some default variables. This makes it
    easier to implement the audit log in models, and makes future changes easier.
    """

    def __init__(self, pk_indexable=True, **kwargs):
        kwargs['to'] = LogEntry

        if pk_indexable:
            kwargs['object_id_field'] = 'object_id'
        else:
            kwargs['object_id_field'] = 'object_pk'

        kwargs['content_type_field'] = 'content_type'
        super(AuditLogHistoryField, self).__init__(**kwargs)
