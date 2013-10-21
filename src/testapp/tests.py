from django.test import TestCase
from testapp.models import SimpleModel


class ModelTest(TestCase):
    def setUp(self):
        self.obj_simple = SimpleModel.objects.create(text='I am not difficult.')

    def test_simple_create(self):
        """Mutations on simple models are logged correctly."""
        # Create the object to work with
        obj = self.obj_simple
        obj.save()

        # Check for log entries
        self.assertTrue(obj.history)
