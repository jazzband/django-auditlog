import datetime
from unittest import mock
from unittest.mock import MagicMock

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.test import TestCase, RequestFactory
from django.utils import timezone

from auditlog.documents import LogEntry, log_created
from auditlog.middleware import AuditlogMiddleware
from auditlog.receivers import log_create, log_update, log_delete
from auditlog.registry import auditlog
from auditlog_tests.models import SimpleModel, AltPrimaryKeyModel, UUIDPrimaryKeyModel, \
    ProxyModel, SimpleIncludeModel, SimpleExcludeModel, SimpleMappingModel, ManyRelatedModel, \
    DateTimeFieldModel, NoDeleteHistoryModel


class BaseTest:
    def setUp(self):
        self.mock_save = MagicMock()
        self.mocked_save = mock.patch('auditlog.documents.LogEntry.save', side_effect=self.mock_save)
        self.mocked_save.start()

    def tearDown(self):
        self.mocked_save.stop()


class BaseModelTest(BaseTest):

    def setUp(self):
        super().setUp()
        self.obj = None
        self.sender = None

    def test_create(self):
        """Creation is logged correctly."""
        self.assertEqual(self.mock_save.call_count, 1)

        loge_entry = log_create(self.sender, self.obj, True)
        self.assertEqual(loge_entry.action, LogEntry.Action.CREATE, msg="Action is 'CREATE'")
        self.assertEqual(loge_entry.object_repr, str(self.obj), msg="Representation is equal")

    def test_update(self):
        """Updates are logged correctly."""
        # Get the object to work with
        obj = self.obj

        # Change something
        obj.boolean = True

        log_entry = log_update(self.sender, obj)

        obj.save()

        self.assertEqual(self.mock_save.call_count, 3)

        # Check for log entries
        self.assertEqual(log_entry.action, LogEntry.Action.UPDATE, msg="There is one log entry for 'UPDATE'")

        self.assertEqual(log_entry.changes, [{"field": "boolean", "old": "False", "new": "True"}],
                         msg="The change is correctly logged")

    def test_delete(self):
        """Deletion is logged correctly."""
        # Get the object to work with
        obj = self.obj

        log_entry = log_delete(self.sender, obj)

        # Delete the object
        obj.delete()

        self.assertEqual(self.mock_save.call_count, 3)

        # Check for log entries
        self.assertEqual(log_entry.action, LogEntry.Action.DELETE, msg="There is one log entry for 'DELETE'")

    def test_recreate(self):
        self.sender.objects.all().delete()
        self.setUp()
        self.test_create()


class SimpleModelTest(BaseModelTest, TestCase):

    def setUp(self):
        super().setUp()
        self.sender = SimpleModel
        self.obj = SimpleModel.objects.create(text='I am not difficult.')


class AltPrimaryKeyModelTest(BaseModelTest, TestCase):
    def setUp(self):
        super().setUp()
        self.sender = AltPrimaryKeyModel
        self.obj = AltPrimaryKeyModel.objects.create(key=str(datetime.datetime.now()), text='I am strange.')


class UUIDPrimaryKeyModelModelTest(BaseModelTest, TestCase):
    def setUp(self):
        super().setUp()
        self.sender = UUIDPrimaryKeyModel
        self.obj = UUIDPrimaryKeyModel.objects.create(text='I am strange.')


class ProxyModelTest(BaseModelTest, TestCase):
    def setUp(self):
        super().setUp()
        self.sender = ProxyModel
        self.obj = ProxyModel.objects.create(text='I am not what you think.')


class ManyRelatedModelTest(BaseTest, TestCase):
    """
    Test the behaviour of a many-to-many relationship.
    """

    def setUp(self):
        super().setUp()
        self.obj = ManyRelatedModel.objects.create()
        self.rel_obj = ManyRelatedModel.objects.create()
        self.obj.related.add(self.rel_obj)

    def test_related(self):
        self.assertEqual(self.mock_save.call_count, 2)


class MiddlewareTest(TestCase):
    """
    Test the middleware responsible for connecting and disconnecting the signals used in automatic logging.
    """

    def setUp(self):
        self.middleware = AuditlogMiddleware()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='test', email='test@example.com', password='top_secret')

    def test_request(self):
        """The actor will be logged."""
        # Create a request
        request = self.factory.get('/')
        request.user = self.user
        # Run middleware
        self.middleware.process_request(request)

        # Validate result
        self.assertTrue(log_created.has_listeners(LogEntry))

        # Finalize transaction
        self.middleware.process_exception(request, None)

    def test_response(self):
        """The signal will be disconnected when the request is processed."""
        # Create a request
        request = self.factory.get('/')
        request.user = self.user

        # Run middleware
        self.middleware.process_request(request)
        self.assertTrue(
            log_created.has_listeners(LogEntry))  # The signal should be present before trying to disconnect it.
        self.middleware.process_response(request, HttpResponse())

        # Validate result
        self.assertFalse(log_created.has_listeners(LogEntry))

    def test_exception(self):
        """The signal will be disconnected when an exception is raised."""
        # Create a request
        request = self.factory.get('/')
        request.user = self.user

        # Run middleware
        self.middleware.process_request(request)
        self.assertTrue(
            log_created.has_listeners(LogEntry))  # The signal should be present before trying to disconnect it.
        self.middleware.process_exception(request, ValidationError("Test"))

        # Validate result
        self.assertFalse(log_created.has_listeners(LogEntry))


class SimpeIncludeModelTest(BaseTest, TestCase):
    """Log only changes in include_fields"""

    def test_register_include_fields(self):
        sim = SimpleIncludeModel(label='Include model', text='Looong text')
        sim.save()
        self.assertTrue(self.mock_save.call_count == 1, msg="There is one log entry")

        # Change label, record
        sim.label = 'Changed label'
        sim.save()
        self.assertTrue(self.mock_save.call_count == 2, msg="There are two log entries")

        # Change text, ignore
        sim.text = 'Short text'
        sim.save()
        self.assertTrue(self.mock_save.call_count == 2, msg="There are two log entries")


class SimpeExcludeModelTest(BaseTest, TestCase):
    """Log only changes that are not in exclude_fields"""

    def test_register_exclude_fields(self):
        sem = SimpleExcludeModel(label='Exclude model', text='Looong text')
        sem.save()
        self.assertTrue(self.mock_save.call_count == 1, msg="There is one log entry")

        # Change label, ignore
        sem.label = 'Changed label'
        sem.save()
        self.assertTrue(self.mock_save.call_count == 2, msg="There are two log entries")

        # Change text, record
        sem.text = 'Short text'
        sem.save()
        self.assertTrue(self.mock_save.call_count == 2, msg="There are two log entries")


class SimpleMappingModelTest(BaseTest, TestCase):
    """Diff displays fields as mapped field names where available through mapping_fields"""

    def test_register_mapping_fields(self):
        smm = SimpleMappingModel(sku='ASD301301A6', vtxt='2.1.5', not_mapped='Not mapped')
        smm.save()

        log_entry = log_create(SimpleMappingModel, smm, True)

        self.assertIn(
            {'field': 'sku', 'old': 'None', 'new': 'ASD301301A6'},
            log_entry.changes,
            msg="The diff function retains 'sku' and can be retrieved."
        )
        self.assertIn(
            {'field': 'not_mapped', 'old': 'None', 'new': 'Not mapped'},
            log_entry.changes,
            msg="The diff function does not map 'not_mapped' and can be retrieved."
        )


class DateTimeFieldModelTest(BaseTest, TestCase):
    """Tests if DateTimeField changes are recognised correctly"""

    utc_plus_one = timezone.get_fixed_timezone(datetime.timedelta(hours=1))
    now = timezone.now()

    def test_model_with_same_time(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(label='DateTimeField model', timestamp=timestamp, date=date, time=time,
                                 naive_dt=self.now)
        dtm.save()
        self.assertTrue(self.mock_save.call_count == 1, msg="There is one log entry")

        # Change timestamp to same datetime and timezone
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        dtm.timestamp = timestamp
        dtm.date = datetime.date(2017, 1, 10)
        dtm.time = datetime.time(12, 0)
        dtm.save()

        # Nothing should have changed
        self.assertTrue(self.mock_save.call_count == 1, msg="There is one log entry")

    def test_model_with_different_timezone(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(label='DateTimeField model', timestamp=timestamp, date=date, time=time,
                                 naive_dt=self.now)
        dtm.save()
        self.assertTrue(self.mock_save.call_count == 1, msg="There is one log entry")

        # Change timestamp to same datetime in another timezone
        timestamp = datetime.datetime(2017, 1, 10, 13, 0, tzinfo=self.utc_plus_one)
        dtm.timestamp = timestamp
        dtm.save()

        # Nothing should have changed
        self.assertTrue(self.mock_save.call_count == 1, msg="There is one log entry")

    def test_model_with_different_datetime(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(label='DateTimeField model', timestamp=timestamp, date=date, time=time,
                                 naive_dt=self.now)
        dtm.save()
        self.assertTrue(self.mock_save.call_count == 1, msg="There is one log entry")

        # Change timestamp to another datetime in the same timezone
        timestamp = datetime.datetime(2017, 1, 10, 13, 0, tzinfo=timezone.utc)
        dtm.timestamp = timestamp
        dtm.save()

        # The time should have changed.
        self.assertTrue(self.mock_save.call_count == 2, msg="There are two log entries")

    def test_model_with_different_date(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(label='DateTimeField model', timestamp=timestamp, date=date, time=time,
                                 naive_dt=self.now)
        dtm.save()
        self.assertTrue(self.mock_save.call_count == 1, msg="There is one log entry")

        # Change timestamp to another datetime in the same timezone
        date = datetime.datetime(2017, 1, 11)
        dtm.date = date
        dtm.save()

        # The time should have changed.
        self.assertTrue(self.mock_save.call_count == 2, msg="There are two log entries")

    def test_model_with_different_time(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(label='DateTimeField model', timestamp=timestamp, date=date, time=time,
                                 naive_dt=self.now)
        dtm.save()
        self.assertTrue(self.mock_save.call_count == 1, msg="There is one log entry")

        # Change timestamp to another datetime in the same timezone
        time = datetime.time(6, 0)
        dtm.time = time
        dtm.save()

        # The time should have changed.
        self.assertTrue(self.mock_save.call_count == 2, msg="There are two log entries")

    def test_model_with_different_time_and_timezone(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(label='DateTimeField model', timestamp=timestamp, date=date, time=time,
                                 naive_dt=self.now)
        dtm.save()
        self.assertTrue(self.mock_save.call_count == 1, msg="There is one log entry")

        # Change timestamp to another datetime and another timezone
        timestamp = datetime.datetime(2017, 1, 10, 14, 0, tzinfo=self.utc_plus_one)
        dtm.timestamp = timestamp
        dtm.save()

        # The time should have changed.
        self.assertTrue(self.mock_save.call_count == 2, msg="There are two log entries")

    def test_update_naive_dt(self):
        timestamp = datetime.datetime(2017, 1, 10, 15, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(label='DateTimeField model', timestamp=timestamp, date=date, time=time,
                                 naive_dt=self.now)
        dtm.save()

        # Change with naive field doesnt raise error
        dtm.naive_dt = timezone.make_naive(timezone.now(), timezone=timezone.utc)
        dtm.save()


class UnregisterTest(BaseTest, TestCase):
    def setUp(self):
        super().setUp()
        auditlog.unregister(SimpleModel)
        self.obj = SimpleModel.objects.create(text='No history')

    def tearDown(self):
        super().tearDown()
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
        self.assertTrue(self.mock_save.call_count == 0, msg="There are no log entries")


@mock.patch('auditlog.documents.LogEntry.get')
@mock.patch('auditlog.documents.LogEntry.search')
class AdminPanelTest(BaseTest, TestCase):

    def setUp(self):
        super().setUp()
        self.username = "test_admin"
        self.password = User.objects.make_random_password()
        self.user, created = User.objects.get_or_create(username=self.username)
        self.user.set_password(self.password)
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.is_active = True
        self.user.save()
        self.obj = SimpleModel.objects.create(text='For admin logentry test')

    def test_auditlog_admin(self, search_mock, get_mock):
        get_mock.return_value = log_create(LogEntry, self.obj, True)
        self.client.login(username=self.username, password=self.password)
        res = self.client.get("/admin/auditlog/logmodel/")
        self.assertEqual(res.status_code, 200)
        res = self.client.get("/admin/auditlog/logmodel/{}/".format('123'), follow=True)
        self.assertEqual(res.status_code, 200)


class NoDeleteHistoryTest(BaseTest, TestCase):
    def test_delete_related(self):
        instance = SimpleModel.objects.create(integer=1)
        self.assertEqual(self.mock_save.call_count, 1)
        instance.integer = 2
        instance.save()
        self.assertEqual(self.mock_save.call_count, 2)

        instance.delete()
        self.assertEqual(self.mock_save.call_count, 3)

    def test_no_delete_related(self):
        instance = NoDeleteHistoryModel.objects.create(integer=1)
        self.assertEqual(self.mock_save.call_count, 1)
        instance.integer = 2
        instance.save()
        self.assertEqual(self.mock_save.call_count, 2)

        instance.delete()
        self.assertEqual(self.mock_save.call_count, 3)
