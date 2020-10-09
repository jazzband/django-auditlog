from elasticsearch.helpers import bulk
from elasticsearch_dsl import Document, connections, Keyword, Date, Nested, InnerDoc, Text

# Define a default Elasticsearch client
connections.create_connection(hosts=['localhost'])


class Change(InnerDoc):
    field = Keyword(required=True)
    old = Text()
    new = Text()


class LogEntry(Document):

    class Action:
        CREATE = 'create'
        UPDATE = 'update'
        DELETE = 'delete'

    action = Keyword(required=True)

    content_type_id = Keyword(required=True)
    content_type_app_label = Keyword(required=True)
    content_type_model = Keyword(required=True)

    object_id = Keyword(required=True)
    object_pk = Keyword()
    object_repr = Keyword(required=True)

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

    @staticmethod
    def bulk(client, documents):
        actions = (i.to_dict(True) for i in documents)
        return bulk(client, actions)
