from elasticsearch_dsl import Document, connections, Keyword, Ip, Date, Nested, InnerDoc, Text
from elasticsearch.helpers import bulk

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
    object_repr = Keyword(required=True)

    actor_id = Keyword()
    actor_email = Keyword()

    remote_addr = Ip()

    timestamp = Date()

    changes = Nested(Change)

    class Index:
        name = 'logs'

    @staticmethod
    def bulk(client, documents):
        actions = (i.to_dict(True) for i in documents)
        return bulk(client, actions)
