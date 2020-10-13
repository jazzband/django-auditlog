from elasticsearch.helpers import bulk
from elasticsearch_dsl import Document, connections, Keyword, Date, Nested, InnerDoc, Text

# Define a default Elasticsearch client
connections.create_connection(hosts=['localhost'])


MAX = 75


class Change(InnerDoc):
    field = Keyword(required=True)
    old = Text()
    new = Text()


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
    actor_pk = Keyword()
    actor_email = Keyword()
    actor_first_name = Text()
    actor_last_name = Text()

    remote_addr = Text()

    timestamp = Date()

    changes = Nested(Change)

    class Index:
        name = 'logs-dealflow'

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
