from django.test import TestCase
from auditlog.models import LogEntry
from testapp.models import SimpleModel


class ModelTest(TestCase):
    def setUp(self):
        self.obj_simple = SimpleModel.objects.create(text='I am not difficult.')

    def test_create(self):
        """Creation is logged correctly."""
        # Get the object to work with
        obj = self.obj_simple

        # Check for log entries
        self.assertTrue(obj.history.count() == 1, msg="There is one log entry")

        try:
            history = obj.history.get()
        except LogEntry.DoesNotExist:
            self.assertTrue(False, "Log entry exists")
        else:
            self.assertEqual(history.action, LogEntry.Action.CREATE, msg="Action is 'CREATE'")
            self.assertEqual(history.object_repr, str(obj), msg="Representation is equal")

    def test_update(self):
        """Updates are logged correctly."""
        # Get the object to work with
        obj = self.obj_simple

        # Change something
        obj.boolean = True
        obj.save()

        # Check for log entries
        self.assertTrue(obj.history.filter(action=LogEntry.Action.UPDATE).count() == 1, msg="There is one log entry for 'UPDATE'")

        history = obj.history.get(action=LogEntry.Action.UPDATE)

        self.assertJSONEqual(history.changes, '{"boolean": ["False", "True"]}', msg="The change is correctly logged")
