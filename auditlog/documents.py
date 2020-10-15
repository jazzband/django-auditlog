from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.dispatch import Signal
from django.utils import timezone
from django.utils.encoding import smart_str
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Document, connections, Keyword, Date, Nested, InnerDoc, Text

# Define a default Elasticsearch client
connections.create_connection(hosts=['localhost'])


MAX = 75


class Change(InnerDoc):
    field = Keyword(required=True)
    old = Text()
    new = Text()


log_created = Signal()


class LogEntry(Document):

    class Action:
        CREATE = 'create'
        UPDATE = 'update'
        DELETE = 'delete'

        choices = (
            (CREATE, CREATE),
            (UPDATE, UPDATE),
            (DELETE, DELETE)
        )

    action = Keyword(required=True)

    content_type_id = Keyword(required=True)
    content_type_app_label = Keyword(required=True)
    content_type_model = Keyword(required=True)

    object_id = Keyword(required=True)
    object_pk = Keyword()
    object_repr = Text(required=True)

    actor_id = Keyword()
    actor_email = Keyword()
    actor_first_name = Text()
    actor_last_name = Text()

    remote_addr = Text()

    timestamp = Date(required=True)

    changes = Nested(Change)

    class Index:
        name = settings.AUDITLOG_INDEX_NAME

    @property
    def actor(self):
        if self.actor_email:
            if self.actor_first_name and self.actor_last_name:
                return f'{self.actor_first_name} {self.actor_last_name} ({self.actor_email})'
            return self.actor_email
        return None

    @property
    def changed_fields(self):
        if self.action == LogEntry.Action.DELETE:
            return ''  # delete
        changes = self.changes
        s = '' if len(changes) == 1 else 's'
        fields = ', '.join(change['field'] for change in changes)
        if len(fields) > MAX:
            i = fields.rfind(' ', 0, MAX)
            fields = fields[:i] + ' ..'
        return '%d change%s: %s' % (len(changes), s, fields)

    @staticmethod
    def bulk(client, documents):
        actions = (i.to_dict(True) for i in documents)
        return bulk(client, actions)

    def __str__(self):
        if self.action == self.Action.CREATE:
            fstring = "Created {repr:s}"
        elif self.action == self.Action.UPDATE:
            fstring = "Updated {repr:s}"
        elif self.action == self.Action.DELETE:
            fstring = "Deleted {repr:s}"
        else:
            fstring = "Logged {repr:s}"

        return fstring.format(repr=self.object_repr)

    @classmethod
    def log_create(cls, instance, **kwargs):
        """
        Helper method to create a new log entry. This method automatically populates some fields when no explicit value
        is given.

        :param instance: The model instance to log a change for.
        :type instance: Model
        :param kwargs: Field overrides for the :py:class:`LogEntry` object.
        :return: The new log entry or `None` if there were no changes.
        :rtype: LogEntry
        """
        changes = kwargs.get('changes', None)
        pk = cls._get_pk_value(instance)

        if changes is not None:
            content_type = ContentType.objects.get_for_model(instance)
            kwargs.setdefault('content_type_id', content_type.id)
            kwargs.setdefault('content_type_app_label', content_type.app_label)
            kwargs.setdefault('content_type_model', content_type.model)
            kwargs.setdefault('object_pk', pk)
            kwargs.setdefault('object_repr', smart_str(instance))
            kwargs.setdefault('timestamp', timezone.now())

            if isinstance(pk, int):
                kwargs.setdefault('object_id', pk)
            log_entry = cls(**kwargs)
            log_created.send(cls, instance=log_entry)
            log_entry.save()
            return log_entry
        return None

    @classmethod
    def _get_pk_value(cls, instance):
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
            pk = cls._get_pk_value(pk)
        return pk
