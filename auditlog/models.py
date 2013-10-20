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
        if not 'content_type' in kwargs:
            kwargs['content_type'] = ContentType.objects.get_for_model(instance)
        if not 'object_pk' in kwargs:
            kwargs['object_pk'] = instance.pk
        if not 'object_id' in kwargs:
            pk_field = instance._meta.pk.name
            pk = getattr(instance, pk_field, None)
            if isinstance(pk, int):
                kwargs['object_id'] = pk

        self.create(**kwargs)


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
    actor = models.ForeignKey('auth.User', blank=True, null=True, on_delete=models.SET_NULL, related_name='+', verbose_name=_("actor"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("timestamp"))

    class Meta:
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']
        verbose_name = _("log entry")
        verbose_name_plural = _("log entries")

    def __unicode__(self):
        if self.action == self.Action.CREATE:
            return _("Created {repr:s}").format(self.object_repr)
        elif self.action == self.Action.UPDATE:
            return _("Updated {repr:s}").format(self.object_repr)
        elif self.action == self.Action.DELETE:
            return _("Deleted {repr:s}").format(self.object_repr)
        else:
            return u'{verbose_name:s} #{id:s}'.format(verbose_name=self._meta.verbose_name.capitalize(), id=self.id)


class AuditLogHistoryField(generic.GenericRelation):
    """
    A subclass of django.contrib.contenttypes.generic.GenericRelation that sets some default variables. This makes it
    easier to implement the audit log in models, and makes future changes easier.
    """

    def __init__(self, **kwargs):
        kwargs['to'] = LogEntry
        kwargs['object_id_field'] = 'object_id'
        kwargs['content_type_field'] = 'content_type'
        super(AuditLogHistoryField, self).__init__(**kwargs)
