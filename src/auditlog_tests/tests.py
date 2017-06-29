import datetime
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.http import HttpResponse
from django.test import TestCase, RequestFactory
from django.utils import timezone

from auditlog.middleware import AuditlogMiddleware
from auditlog.models import LogEntry
from auditlog.registry import auditlog
from auditlog_tests.models import SimpleModel, AltPrimaryKeyModel, UUIDPrimaryKeyModel, \
    ProxyModel, SimpleIncludeModel, SimpleExcludeModel, RelatedModel, ManyRelatedModel, \
    AdditionalDataIncludedModel, DateTimeFieldModel


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


class UUIDPrimaryKeyModelModelTest(SimpleModelTest):
    def setUp(self):
        self.obj = UUIDPrimaryKeyModel.objects.create(text='I am strange.')

    def test_get_for_object(self):
        self.obj.boolean = True
        self.obj.save()

        self.assertEqual(LogEntry.objects.get_for_object(self.obj).count(), 2)

    def test_get_for_objects(self):
        self.obj.boolean = True
        self.obj.save()

        self.assertEqual(LogEntry.objects.get_for_objects(UUIDPrimaryKeyModel.objects.all()).count(), 2)


class ProxyModelTest(SimpleModelTest):
    def setUp(self):
        self.obj = ProxyModel.objects.create(text='I am not what you think.')


class ManyRelatedModelTest(TestCase):
    """
    Test the behaviour of a many-to-many relationship.
    """
    def setUp(self):
        self.obj = ManyRelatedModel.objects.create()
        self.rel_obj = ManyRelatedModel.objects.create()
        self.obj.related.add(self.rel_obj)

    def test_related(self):
        self.assertEqual(LogEntry.objects.get_for_objects(self.obj.related.all()).count(), self.rel_obj.history.count())
        self.assertEqual(LogEntry.objects.get_for_objects(self.obj.related.all()).first(), self.rel_obj.history.first())


class MiddlewareTest(TestCase):
    """
    Test the middleware responsible for connecting and disconnecting the signals used in automatic logging.
    """
    def setUp(self):
        self.middleware = AuditlogMiddleware()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='test', email='test@example.com', password='top_secret')

    def test_request_anonymous(self):
        """No actor will be logged when a user is not logged in."""
        # Create a request
        request = self.factory.get('/')
        request.user = AnonymousUser()

        # Run middleware
        self.middleware.process_request(request)

        # Validate result
        self.assertFalse(pre_save.has_listeners(LogEntry))

        # Finalize transaction
        self.middleware.process_exception(request, None)

    def test_request(self):
        """The actor will be logged when a user is logged in."""
        # Create a request
        request = self.factory.get('/')
        request.user = self.user
        # Run middleware
        self.middleware.process_request(request)

        # Validate result
        self.assertTrue(pre_save.has_listeners(LogEntry))

        # Finalize transaction
        self.middleware.process_exception(request, None)

    def test_response(self):
        """The signal will be disconnected when the request is processed."""
        # Create a request
        request = self.factory.get('/')
        request.user = self.user

        # Run middleware
        self.middleware.process_request(request)
        self.assertTrue(pre_save.has_listeners(LogEntry))  # The signal should be present before trying to disconnect it.
        self.middleware.process_response(request, HttpResponse())

        # Validate result
        self.assertFalse(pre_save.has_listeners(LogEntry))

    def test_exception(self):
        """The signal will be disconnected when an exception is raised."""
        # Create a request
        request = self.factory.get('/')
        request.user = self.user

        # Run middleware
        self.middleware.process_request(request)
        self.assertTrue(pre_save.has_listeners(LogEntry))  # The signal should be present before trying to disconnect it.
        self.middleware.process_exception(request, ValidationError("Test"))

        # Validate result
        self.assertFalse(pre_save.has_listeners(LogEntry))


class SimpeIncludeModelTest(TestCase):
    """Log only changes in include_fields"""

    def test_register_include_fields(self):
        sim = SimpleIncludeModel(label='Include model', text='Looong text')
        sim.save()
        self.assertTrue(sim.history.count() == 1, msg="There is one log entry")

        # Change label, record
        sim.label = 'Changed label'
        sim.save()
        self.assertTrue(sim.history.count() == 2, msg="There are two log entries")

        # Change text, ignore
        sim.text = 'Short text'
        sim.save()
        self.assertTrue(sim.history.count() == 2, msg="There are two log entries")


class SimpeExcludeModelTest(TestCase):
    """Log only changes that are not in exclude_fields"""

    def test_register_exclude_fields(self):
        sem = SimpleExcludeModel(label='Exclude model', text='Looong text')
        sem.save()
        self.assertTrue(sem.history.count() == 1, msg="There is one log entry")

        # Change label, ignore
        sem.label = 'Changed label'
        sem.save()
        self.assertTrue(sem.history.count() == 2, msg="There are two log entries")

        # Change text, record
        sem.text = 'Short text'
        sem.save()
        self.assertTrue(sem.history.count() == 2, msg="There are two log entries")


class AdditionalDataModelTest(TestCase):
    """Log additional data if get_additional_data is defined in the model"""

    def test_model_without_additional_data(self):
        obj_wo_additional_data = SimpleModel.objects.create(text='No additional '
                                                                 'data')
        obj_log_entry = obj_wo_additional_data.history.get()
        self.assertIsNone(obj_log_entry.additional_data)

    def test_model_with_additional_data(self):
        related_model = SimpleModel.objects.create(text='Log my reference')
        obj_with_additional_data = AdditionalDataIncludedModel(
            label='Additional data to log entries', related=related_model)
        obj_with_additional_data.save()
        self.assertTrue(obj_with_additional_data.history.count() == 1,
                        msg="There is 1 log entry")
        log_entry = obj_with_additional_data.history.get()
        self.assertIsNotNone(log_entry.additional_data)
        extra_data = log_entry.additional_data
        self.assertTrue(extra_data['related_model_text'] == related_model.text,
                        msg="Related model's text is logged")
        self.assertTrue(extra_data['related_model_id'] == related_model.id,
                        msg="Related model's id is logged")


class DateTimeFieldModelTest(TestCase):
    """Tests if DateTimeField changes are recognised correctly"""

    utc_plus_one = timezone.get_fixed_timezone(datetime.timedelta(hours=1))

    def test_model_with_same_time(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        dtm = DateTimeFieldModel(label='DateTimeField model', timestamp=timestamp)
        dtm.save()
        self.assertTrue(dtm.history.count() == 1, msg="There is one log entry")

        # Change timestamp to same datetime and timezone
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        dtm.timestamp = timestamp
        dtm.save()

        # Nothing should have changed
        self.assertTrue(dtm.history.count() == 1, msg="There is one log entry")

    def test_model_with_different_timezone(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        dtm = DateTimeFieldModel(label='DateTimeField model', timestamp=timestamp)
        dtm.save()
        self.assertTrue(dtm.history.count() == 1, msg="There is one log entry")

        # Change timestamp to same datetime in another timezone
        timestamp = datetime.datetime(2017, 1, 10, 13, 0, tzinfo=self.utc_plus_one)
        dtm.timestamp = timestamp
        dtm.save()

        # Nothing should have changed
        self.assertTrue(dtm.history.count() == 1, msg="There is one log entry")

    def test_model_with_different_time(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        dtm = DateTimeFieldModel(label='DateTimeField model', timestamp=timestamp)
        dtm.save()
        self.assertTrue(dtm.history.count() == 1, msg="There is one log entry")

        # Change timestamp to another datetime in the same timezone
        timestamp = datetime.datetime(2017, 1, 10, 13, 0, tzinfo=timezone.utc)
        dtm.timestamp = timestamp
        dtm.save()

        # The time should have changed.
        self.assertTrue(dtm.history.count() == 2, msg="There are two log entries")

    def test_model_with_different_time_and_timezone(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        dtm = DateTimeFieldModel(label='DateTimeField model', timestamp=timestamp)
        dtm.save()
        self.assertTrue(dtm.history.count() == 1, msg="There is one log entry")

        # Change timestamp to another datetime and another timezone
        timestamp = datetime.datetime(2017, 1, 10, 14, 0, tzinfo=self.utc_plus_one)
        dtm.timestamp = timestamp
        dtm.save()

        # The time should have changed.
        self.assertTrue(dtm.history.count() == 2, msg="There are two log entries")


class UnregisterTest(TestCase):
    def setUp(self):
        auditlog.unregister(SimpleModel)
        self.obj = SimpleModel.objects.create(text='No history')

    def tearDown(self):
        # Re-register for future tests
        auditlog.register(SimpleModel)

    def test_unregister_create(self):
        """Creation is not logged after unregistering."""
        # Get the object to work with
        obj = self.obj

        # Check for log entries
        self.assertTrue(obj.history.count() == 0, msg="There are no log entries")

    def test_unregister_update(self):
        """Updates are not logged after unregistering."""
        # Get the object to work with
        obj = self.obj

        # Change something
        obj.boolean = True
        obj.save()

        # Check for log entries
        self.assertTrue(obj.history.count() == 0, msg="There are no log entries")

    def test_unregister_delete(self):
        """Deletion is not logged after unregistering."""
        # Get the object to work with
        obj = self.obj

        # Delete the object
        obj.delete()

        # Check for log entries
        self.assertTrue(LogEntry.objects.count() == 0, msg="There are no log entries")
