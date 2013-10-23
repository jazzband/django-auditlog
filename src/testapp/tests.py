import datetime
from django.test import TestCase
from auditlog.models import LogEntry
from testapp.models import SimpleModel, AltPrimaryKeyModel, ProxyModel


class SimpleModelTest(TestCase):
    def setUp(self):
        self.obj = SimpleModel.objects.create(text='I am not difficult.')

    def test_create(self):
        """Creation is logged correctly."""
        # Get the object to work with
        obj = self.obj

        # Check for log entries
        self.assertTrue(obj.history.count() == 1, msg="There is one log entry")

        try:
            history = obj.history.get()
        except obj.history.DoesNotExist:
            self.assertTrue(False, "Log entry exists")
        else:
            self.assertEqual(history.action, LogEntry.Action.CREATE, msg="Action is 'CREATE'")
            self.assertEqual(history.object_repr, str(obj), msg="Representation is equal")

    def test_update(self):
        """Updates are logged correctly."""
        # Get the object to work with
        obj = self.obj

        # Change something
        obj.boolean = True
        obj.save()

        # Check for log entries
        self.assertTrue(obj.history.filter(action=LogEntry.Action.UPDATE).count() == 1, msg="There is one log entry for 'UPDATE'")

        history = obj.history.get(action=LogEntry.Action.UPDATE)

        self.assertJSONEqual(history.changes, '{"boolean": ["False", "True"]}', msg="The change is correctly logged")

    def test_delete(self):
        """Deletion is logged correctly."""
        # Get the object to work with
        obj = self.obj

        history = obj.history.latest()

        # Delete the object
        obj.delete()

        # Check for log entries
        self.assertTrue(LogEntry.objects.filter(content_type=history.content_type, object_pk=history.object_pk, action=LogEntry.Action.DELETE).count() == 1, msg="There is one log entry for 'DELETE'")

    def test_recreate(self):
        SimpleModel.objects.all().delete()
        self.setUp()
        self.test_create()


class AltPrimaryKeyModelTest(SimpleModelTest):
    def setUp(self):
        self.obj = AltPrimaryKeyModel.objects.create(key=str(datetime.datetime.now()), text='I am strange.')


class ProxyModelTest(SimpleModelTest):
    def setUp(self):
        self.obj = ProxyModel.objects.create(text='I am not what you think.')
