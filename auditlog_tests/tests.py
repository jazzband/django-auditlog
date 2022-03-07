import datetime
import json

import django
from dateutil.tz import gettz
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.utils import dateformat, formats, timezone

from auditlog.diff import model_instance_diff
from auditlog.middleware import AuditlogMiddleware
from auditlog.models import LogEntry
from auditlog.registry import auditlog
from auditlog_tests.models import (
    AdditionalDataIncludedModel,
    AltPrimaryKeyModel,
    CharfieldTextfieldModel,
    ChoicesFieldModel,
    DateTimeFieldModel,
    ManyRelatedModel,
    NoDeleteHistoryModel,
    PostgresArrayFieldModel,
    ProxyModel,
    RelatedModel,
    SimpleExcludeModel,
    SimpleIncludeModel,
    SimpleMappingModel,
    SimpleModel,
    UUIDPrimaryKeyModel,
)


class SimpleModelTest(TestCase):
    def setUp(self):
        self.obj = SimpleModel.objects.create(text="I am not difficult.")

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
            self.assertEqual(
                history.action, LogEntry.Action.CREATE, msg="Action is 'CREATE'"
            )
            self.assertEqual(
                history.object_repr, str(obj), msg="Representation is equal"
            )

    def test_update(self):
        """Updates are logged correctly."""
        # Get the object to work with
        obj = self.obj

        # Change something
        obj.boolean = True
        obj.save()

        # Check for log entries
        self.assertTrue(
            obj.history.filter(action=LogEntry.Action.UPDATE).count() == 1,
            msg="There is one log entry for 'UPDATE'",
        )

        history = obj.history.get(action=LogEntry.Action.UPDATE)

        self.assertJSONEqual(
            history.changes,
            '{"boolean": ["False", "True"]}',
            msg="The change is correctly logged",
        )

    def test_update_specific_field_supplied_via_save_method(self):
        obj = self.obj

        # Change 2 fields, but save one only.
        obj.boolean = True
        obj.text = "Short text"
        obj.save(update_fields=["boolean"])

        # This implicitly asserts there is only one UPDATE change since the `.get` would fail otherwise.
        self.assertJSONEqual(
            obj.history.get(action=LogEntry.Action.UPDATE).changes,
            '{"boolean": ["False", "True"]}',
            msg="Object modifications that are not saved to DB are not logged when using the `update_fields`.",
        )

    def test_django_update_fields_edge_cases(self):
        """
        The test ensures that if Django's `update_fields` behavior ever changes for special values `(None, [])`, the
        package should too. https://docs.djangoproject.com/en/3.2/ref/models/instances/#specifying-which-fields-to-save
        """
        obj = self.obj

        # Change boolean, but save no changes by passing an empty list.
        obj.boolean = True
        obj.save(update_fields=[])

        self.assertTrue(
            obj.history.filter(action=LogEntry.Action.UPDATE).count() == 0,
            msg="There is no log entries created",
        )
        obj.refresh_from_db()
        self.assertFalse(obj.boolean)  # Change didn't persist in DB as expected.

        # Passing `None` should save both fields according to Django.
        obj.integer = 1
        obj.boolean = True
        obj.save(update_fields=None)
        self.assertJSONEqual(
            obj.history.get(action=LogEntry.Action.UPDATE).changes,
            '{"boolean": ["False", "True"], "integer": ["None", "1"]}',
            msg="The 2 fields changed are correctly logged",
        )

    def test_delete(self):
        """Deletion is logged correctly."""
        # Get the object to work with
        obj = self.obj

        history = obj.history.latest()

        # Delete the object
        obj.delete()

        # Check for log entries
        self.assertTrue(
            LogEntry.objects.filter(
                content_type=history.content_type,
                object_pk=history.object_pk,
                action=LogEntry.Action.DELETE,
            ).count()
            == 1,
            msg="There is one log entry for 'DELETE'",
        )

    def test_recreate(self):
        SimpleModel.objects.all().delete()
        self.setUp()
        self.test_create()

    def test_create_log_to_object_from_other_database(self):
        msg = "The log should not try to write to the same database as the object"

        instance = self.obj
        # simulate object obtained from a different database (read only)
        instance._state.db = "replica"

        changes = model_instance_diff(None, instance)

        log_entry = LogEntry.objects.log_create(
            instance,
            action=LogEntry.Action.CREATE,
            changes=json.dumps(changes),
        )
        self.assertEqual(
            log_entry._state.db, "default", msg=msg
        )  # must be created in default database


class AltPrimaryKeyModelTest(SimpleModelTest):
    def setUp(self):
        self.obj = AltPrimaryKeyModel.objects.create(
            key=str(datetime.datetime.now()), text="I am strange."
        )


class UUIDPrimaryKeyModelModelTest(SimpleModelTest):
    def setUp(self):
        self.obj = UUIDPrimaryKeyModel.objects.create(text="I am strange.")

    def test_get_for_object(self):
        self.obj.boolean = True
        self.obj.save()

        self.assertEqual(LogEntry.objects.get_for_object(self.obj).count(), 2)

    def test_get_for_objects(self):
        self.obj.boolean = True
        self.obj.save()

        self.assertEqual(
            LogEntry.objects.get_for_objects(UUIDPrimaryKeyModel.objects.all()).count(),
            2,
        )


class ProxyModelTest(SimpleModelTest):
    def setUp(self):
        self.obj = ProxyModel.objects.create(text="I am not what you think.")


class ManyRelatedModelTest(TestCase):
    """
    Test the behaviour of a many-to-many relationship.
    """

    def setUp(self):
        self.obj = ManyRelatedModel.objects.create()
        self.rel_obj = ManyRelatedModel.objects.create()
        self.obj.related.add(self.rel_obj)

    def test_related(self):
        self.assertEqual(
            LogEntry.objects.get_for_objects(self.obj.related.all()).count(),
            self.rel_obj.history.count(),
        )
        self.assertEqual(
            LogEntry.objects.get_for_objects(self.obj.related.all()).first(),
            self.rel_obj.history.first(),
        )


class MiddlewareTest(TestCase):
    """
    Test the middleware responsible for connecting and disconnecting the signals used in automatic logging.
    """

    def setUp(self):
        def get_response(request):
            return HttpResponse()

        self.middleware = AuditlogMiddleware(get_response)
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="test", email="test@example.com", password="top_secret"
        )

    def test_request_anonymous(self):
        """No actor will be logged when a user is not logged in."""
        # Create a request
        request = self.factory.get("/")
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
        request = self.factory.get("/")
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
        request = self.factory.get("/")
        request.user = self.user

        # Run middleware
        self.middleware.process_request(request)
        self.assertTrue(
            pre_save.has_listeners(LogEntry)
        )  # The signal should be present before trying to disconnect it.
        self.middleware.process_response(request, HttpResponse())

        # Validate result
        self.assertFalse(pre_save.has_listeners(LogEntry))

    def test_exception(self):
        """The signal will be disconnected when an exception is raised."""
        # Create a request
        request = self.factory.get("/")
        request.user = self.user

        # Run middleware
        self.middleware.process_request(request)
        self.assertTrue(
            pre_save.has_listeners(LogEntry)
        )  # The signal should be present before trying to disconnect it.
        self.middleware.process_exception(request, ValidationError("Test"))

        # Validate result
        self.assertFalse(pre_save.has_listeners(LogEntry))


class SimpleIncludeModelTest(TestCase):
    """Log only changes in include_fields"""

    def test_specified_save_fields_are_ignored_if_not_included(self):
        obj = SimpleIncludeModel.objects.create(label="Initial label", text="Text")
        obj.text = "New text"
        obj.save(update_fields=["text"])

        self.assertTrue(
            obj.history.filter(action=LogEntry.Action.UPDATE).count() == 0,
            msg="Text change was not logged, even when passed explicitly",
        )

        obj.label = "New label"
        obj.text = "Newer text"
        obj.save(update_fields=["text", "label"])

        self.assertJSONEqual(
            obj.history.get(action=LogEntry.Action.UPDATE).changes,
            '{"label": ["Initial label", "New label"]}',
            msg="Only the label was logged, regardless of multiple entries in `update_fields`",
        )

    def test_register_include_fields(self):
        sim = SimpleIncludeModel(label="Include model", text="Looong text")
        sim.save()
        self.assertTrue(sim.history.count() == 1, msg="There is one log entry")

        # Change label, record
        sim.label = "Changed label"
        sim.save()
        self.assertTrue(sim.history.count() == 2, msg="There are two log entries")

        # Change text, ignore
        sim.text = "Short text"
        sim.save()
        self.assertTrue(sim.history.count() == 2, msg="There are two log entries")


class SimpleExcludeModelTest(TestCase):
    """Log only changes that are not in exclude_fields"""

    def test_specified_save_fields_are_excluded_normally(self):
        obj = SimpleExcludeModel.objects.create(label="Exclude model", text="Text")
        obj.text = "New text"
        obj.save(update_fields=["text"])

        self.assertTrue(
            obj.history.filter(action=LogEntry.Action.UPDATE).count() == 0,
            msg="Text change was not logged, even when passed explicitly",
        )

    def test_register_exclude_fields(self):
        sem = SimpleExcludeModel(label="Exclude model", text="Looong text")
        sem.save()
        self.assertTrue(sem.history.count() == 1, msg="There is one log entry")

        # Change label, record it.
        sem.label = "Changed label"
        sem.save()
        self.assertTrue(sem.history.count() == 2, msg="There are two log entries")

        # Change text, ignore it.
        sem.text = "Short text"
        sem.save()
        self.assertTrue(sem.history.count() == 2, msg="There are two log entries")


class SimpleMappingModelTest(TestCase):
    """Diff displays fields as mapped field names where available through mapping_fields"""

    def test_register_mapping_fields(self):
        smm = SimpleMappingModel(
            sku="ASD301301A6", vtxt="2.1.5", not_mapped="Not mapped"
        )
        smm.save()
        self.assertTrue(
            smm.history.latest().changes_dict["sku"][1] == "ASD301301A6",
            msg="The diff function retains 'sku' and can be retrieved.",
        )
        self.assertTrue(
            smm.history.latest().changes_dict["not_mapped"][1] == "Not mapped",
            msg="The diff function does not map 'not_mapped' and can be retrieved.",
        )
        self.assertTrue(
            smm.history.latest().changes_display_dict["Product No."][1]
            == "ASD301301A6",
            msg="The diff function maps 'sku' as 'Product No.' and can be retrieved.",
        )
        self.assertTrue(
            smm.history.latest().changes_display_dict["Version"][1] == "2.1.5",
            msg=(
                "The diff function maps 'vtxt' as 'Version' through verbose_name"
                " setting on the model field and can be retrieved."
            ),
        )
        self.assertTrue(
            smm.history.latest().changes_display_dict["not mapped"][1] == "Not mapped",
            msg=(
                "The diff function uses the django default verbose name for 'not_mapped'"
                " and can be retrieved."
            ),
        )


class AdditionalDataModelTest(TestCase):
    """Log additional data if get_additional_data is defined in the model"""

    def test_model_without_additional_data(self):
        obj_wo_additional_data = SimpleModel.objects.create(
            text="No additional " "data"
        )
        obj_log_entry = obj_wo_additional_data.history.get()
        self.assertIsNone(obj_log_entry.additional_data)

    def test_model_with_additional_data(self):
        related_model = SimpleModel.objects.create(text="Log my reference")
        obj_with_additional_data = AdditionalDataIncludedModel(
            label="Additional data to log entries", related=related_model
        )
        obj_with_additional_data.save()
        self.assertTrue(
            obj_with_additional_data.history.count() == 1, msg="There is 1 log entry"
        )
        log_entry = obj_with_additional_data.history.get()
        extra_data = log_entry.additional_data
        self.assertIsNotNone(extra_data)
        self.assertTrue(
            extra_data["related_model_text"] == related_model.text,
            msg="Related model's text is logged",
        )
        self.assertTrue(
            extra_data["related_model_id"] == related_model.id,
            msg="Related model's id is logged",
        )


class DateTimeFieldModelTest(TestCase):
    """Tests if DateTimeField changes are recognised correctly"""

    utc_plus_one = timezone.get_fixed_timezone(datetime.timedelta(hours=1))
    now = timezone.now()

    def test_model_with_same_time(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(
            label="DateTimeField model",
            timestamp=timestamp,
            date=date,
            time=time,
            naive_dt=self.now,
        )
        dtm.save()
        self.assertTrue(dtm.history.count() == 1, msg="There is one log entry")

        # Change timestamp to same datetime and timezone
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        dtm.timestamp = timestamp
        dtm.date = datetime.date(2017, 1, 10)
        dtm.time = datetime.time(12, 0)
        dtm.save()

        # Nothing should have changed
        self.assertTrue(dtm.history.count() == 1, msg="There is one log entry")

    def test_model_with_different_timezone(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(
            label="DateTimeField model",
            timestamp=timestamp,
            date=date,
            time=time,
            naive_dt=self.now,
        )
        dtm.save()
        self.assertTrue(dtm.history.count() == 1, msg="There is one log entry")

        # Change timestamp to same datetime in another timezone
        timestamp = datetime.datetime(2017, 1, 10, 13, 0, tzinfo=self.utc_plus_one)
        dtm.timestamp = timestamp
        dtm.save()

        # Nothing should have changed
        self.assertTrue(dtm.history.count() == 1, msg="There is one log entry")

    def test_model_with_different_datetime(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(
            label="DateTimeField model",
            timestamp=timestamp,
            date=date,
            time=time,
            naive_dt=self.now,
        )
        dtm.save()
        self.assertTrue(dtm.history.count() == 1, msg="There is one log entry")

        # Change timestamp to another datetime in the same timezone
        timestamp = datetime.datetime(2017, 1, 10, 13, 0, tzinfo=timezone.utc)
        dtm.timestamp = timestamp
        dtm.save()

        # The time should have changed.
        self.assertTrue(dtm.history.count() == 2, msg="There are two log entries")

    def test_model_with_different_date(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(
            label="DateTimeField model",
            timestamp=timestamp,
            date=date,
            time=time,
            naive_dt=self.now,
        )
        dtm.save()
        self.assertTrue(dtm.history.count() == 1, msg="There is one log entry")

        # Change timestamp to another datetime in the same timezone
        date = datetime.datetime(2017, 1, 11)
        dtm.date = date
        dtm.save()

        # The time should have changed.
        self.assertTrue(dtm.history.count() == 2, msg="There are two log entries")

    def test_model_with_different_time(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(
            label="DateTimeField model",
            timestamp=timestamp,
            date=date,
            time=time,
            naive_dt=self.now,
        )
        dtm.save()
        self.assertTrue(dtm.history.count() == 1, msg="There is one log entry")

        # Change timestamp to another datetime in the same timezone
        time = datetime.time(6, 0)
        dtm.time = time
        dtm.save()

        # The time should have changed.
        self.assertTrue(dtm.history.count() == 2, msg="There are two log entries")

    def test_model_with_different_time_and_timezone(self):
        timestamp = datetime.datetime(2017, 1, 10, 12, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(
            label="DateTimeField model",
            timestamp=timestamp,
            date=date,
            time=time,
            naive_dt=self.now,
        )
        dtm.save()
        self.assertTrue(dtm.history.count() == 1, msg="There is one log entry")

        # Change timestamp to another datetime and another timezone
        timestamp = datetime.datetime(2017, 1, 10, 14, 0, tzinfo=self.utc_plus_one)
        dtm.timestamp = timestamp
        dtm.save()

        # The time should have changed.
        self.assertTrue(dtm.history.count() == 2, msg="There are two log entries")

    def test_changes_display_dict_datetime(self):
        timestamp = datetime.datetime(2017, 1, 10, 15, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(
            label="DateTimeField model",
            timestamp=timestamp,
            date=date,
            time=time,
            naive_dt=self.now,
        )
        dtm.save()
        localized_timestamp = timestamp.astimezone(gettz(settings.TIME_ZONE))
        self.assertTrue(
            dtm.history.latest().changes_display_dict["timestamp"][1]
            == dateformat.format(localized_timestamp, settings.DATETIME_FORMAT),
            msg=(
                "The datetime should be formatted according to Django's settings for"
                " DATETIME_FORMAT"
            ),
        )
        timestamp = timezone.now()
        dtm.timestamp = timestamp
        dtm.save()
        localized_timestamp = timestamp.astimezone(gettz(settings.TIME_ZONE))
        self.assertTrue(
            dtm.history.latest().changes_display_dict["timestamp"][1]
            == dateformat.format(localized_timestamp, settings.DATETIME_FORMAT),
            msg=(
                "The datetime should be formatted according to Django's settings for"
                " DATETIME_FORMAT"
            ),
        )

        # Change USE_L10N = True
        with self.settings(USE_L10N=True, LANGUAGE_CODE="en-GB"):
            self.assertTrue(
                dtm.history.latest().changes_display_dict["timestamp"][1]
                == formats.localize(localized_timestamp),
                msg=(
                    "The datetime should be formatted according to Django's settings for"
                    " USE_L10N is True with a different LANGUAGE_CODE."
                ),
            )

    def test_changes_display_dict_date(self):
        timestamp = datetime.datetime(2017, 1, 10, 15, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(
            label="DateTimeField model",
            timestamp=timestamp,
            date=date,
            time=time,
            naive_dt=self.now,
        )
        dtm.save()
        self.assertTrue(
            dtm.history.latest().changes_display_dict["date"][1]
            == dateformat.format(date, settings.DATE_FORMAT),
            msg=(
                "The date should be formatted according to Django's settings for"
                " DATE_FORMAT unless USE_L10N is True."
            ),
        )
        date = datetime.date(2017, 1, 11)
        dtm.date = date
        dtm.save()
        self.assertTrue(
            dtm.history.latest().changes_display_dict["date"][1]
            == dateformat.format(date, settings.DATE_FORMAT),
            msg=(
                "The date should be formatted according to Django's settings for"
                " DATE_FORMAT unless USE_L10N is True."
            ),
        )

        # Change USE_L10N = True
        with self.settings(USE_L10N=True, LANGUAGE_CODE="en-GB"):
            self.assertTrue(
                dtm.history.latest().changes_display_dict["date"][1]
                == formats.localize(date),
                msg=(
                    "The date should be formatted according to Django's settings for"
                    " USE_L10N is True with a different LANGUAGE_CODE."
                ),
            )

    def test_changes_display_dict_time(self):
        timestamp = datetime.datetime(2017, 1, 10, 15, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(
            label="DateTimeField model",
            timestamp=timestamp,
            date=date,
            time=time,
            naive_dt=self.now,
        )
        dtm.save()
        self.assertTrue(
            dtm.history.latest().changes_display_dict["time"][1]
            == dateformat.format(time, settings.TIME_FORMAT),
            msg=(
                "The time should be formatted according to Django's settings for"
                " TIME_FORMAT unless USE_L10N is True."
            ),
        )
        time = datetime.time(6, 0)
        dtm.time = time
        dtm.save()
        self.assertTrue(
            dtm.history.latest().changes_display_dict["time"][1]
            == dateformat.format(time, settings.TIME_FORMAT),
            msg=(
                "The time should be formatted according to Django's settings for"
                " TIME_FORMAT unless USE_L10N is True."
            ),
        )

        # Change USE_L10N = True
        with self.settings(USE_L10N=True, LANGUAGE_CODE="en-GB"):
            self.assertTrue(
                dtm.history.latest().changes_display_dict["time"][1]
                == formats.localize(time),
                msg=(
                    "The time should be formatted according to Django's settings for"
                    " USE_L10N is True with a different LANGUAGE_CODE."
                ),
            )

    def test_update_naive_dt(self):
        timestamp = datetime.datetime(2017, 1, 10, 15, 0, tzinfo=timezone.utc)
        date = datetime.date(2017, 1, 10)
        time = datetime.time(12, 0)
        dtm = DateTimeFieldModel(
            label="DateTimeField model",
            timestamp=timestamp,
            date=date,
            time=time,
            naive_dt=self.now,
        )
        dtm.save()

        # Change with naive field doesnt raise error
        dtm.naive_dt = timezone.make_naive(timezone.now(), timezone=timezone.utc)
        dtm.save()


class UnregisterTest(TestCase):
    def setUp(self):
        auditlog.unregister(SimpleModel)
        self.obj = SimpleModel.objects.create(text="No history")

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


class ChoicesFieldModelTest(TestCase):
    def setUp(self):
        self.obj = ChoicesFieldModel.objects.create(
            status=ChoicesFieldModel.RED,
            multiplechoice=[
                ChoicesFieldModel.RED,
                ChoicesFieldModel.YELLOW,
                ChoicesFieldModel.GREEN,
            ],
        )

    def test_changes_display_dict_single_choice(self):

        self.assertTrue(
            self.obj.history.latest().changes_display_dict["status"][1] == "Red",
            msg="The human readable text 'Red' is displayed.",
        )
        self.obj.status = ChoicesFieldModel.GREEN
        self.obj.save()
        self.assertTrue(
            self.obj.history.latest().changes_display_dict["status"][1] == "Green",
            msg="The human readable text 'Green' is displayed.",
        )

    def test_changes_display_dict_multiplechoice(self):
        self.assertTrue(
            self.obj.history.latest().changes_display_dict["multiplechoice"][1]
            == "Red, Yellow, Green",
            msg="The human readable text 'Red, Yellow, Green' is displayed.",
        )
        self.obj.multiplechoice = ChoicesFieldModel.RED
        self.obj.save()
        self.assertTrue(
            self.obj.history.latest().changes_display_dict["multiplechoice"][1]
            == "Red",
            msg="The human readable text 'Red' is displayed.",
        )


class CharfieldTextfieldModelTest(TestCase):
    def setUp(self):
        self.PLACEHOLDER_LONGCHAR = "s" * 255
        self.PLACEHOLDER_LONGTEXTFIELD = "s" * 1000
        self.obj = CharfieldTextfieldModel.objects.create(
            longchar=self.PLACEHOLDER_LONGCHAR,
            longtextfield=self.PLACEHOLDER_LONGTEXTFIELD,
        )

    def test_changes_display_dict_longchar(self):
        self.assertTrue(
            self.obj.history.latest().changes_display_dict["longchar"][1]
            == f"{self.PLACEHOLDER_LONGCHAR[:140]}...",
            msg="The string should be truncated at 140 characters with an ellipsis at the end.",
        )
        SHORTENED_PLACEHOLDER = self.PLACEHOLDER_LONGCHAR[:139]
        self.obj.longchar = SHORTENED_PLACEHOLDER
        self.obj.save()
        self.assertTrue(
            self.obj.history.latest().changes_display_dict["longchar"][1]
            == SHORTENED_PLACEHOLDER,
            msg="The field should display the entire string because it is less than 140 characters",
        )

    def test_changes_display_dict_longtextfield(self):
        self.assertTrue(
            self.obj.history.latest().changes_display_dict["longtextfield"][1]
            == f"{self.PLACEHOLDER_LONGTEXTFIELD[:140]}...",
            msg="The string should be truncated at 140 characters with an ellipsis at the end.",
        )
        SHORTENED_PLACEHOLDER = self.PLACEHOLDER_LONGTEXTFIELD[:139]
        self.obj.longtextfield = SHORTENED_PLACEHOLDER
        self.obj.save()
        self.assertTrue(
            self.obj.history.latest().changes_display_dict["longtextfield"][1]
            == SHORTENED_PLACEHOLDER,
            msg="The field should display the entire string because it is less than 140 characters",
        )


class PostgresArrayFieldModelTest(TestCase):
    databases = "__all__"

    def setUp(self):
        self.obj = PostgresArrayFieldModel.objects.create(
            arrayfield=[PostgresArrayFieldModel.RED, PostgresArrayFieldModel.GREEN],
        )

    @property
    def latest_array_change(self):
        return self.obj.history.latest().changes_display_dict["arrayfield"][1]

    def test_changes_display_dict_arrayfield(self):
        self.assertTrue(
            self.latest_array_change == "Red, Green",
            msg="The human readable text for the two choices, 'Red, Green' is displayed.",
        )
        self.obj.arrayfield = [PostgresArrayFieldModel.GREEN]
        self.obj.save()
        self.assertTrue(
            self.latest_array_change == "Green",
            msg="The human readable text 'Green' is displayed.",
        )
        self.obj.arrayfield = []
        self.obj.save()
        self.assertTrue(
            self.latest_array_change == "",
            msg="The human readable text '' is displayed.",
        )
        self.obj.arrayfield = [PostgresArrayFieldModel.GREEN]
        self.obj.save()
        self.assertTrue(
            self.latest_array_change == "Green",
            msg="The human readable text 'Green' is displayed.",
        )


class AdminPanelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = "test_admin"
        cls.password = User.objects.make_random_password()
        cls.user, created = User.objects.get_or_create(username=cls.username)
        cls.user.set_password(cls.password)
        cls.user.is_staff = True
        cls.user.is_superuser = True
        cls.user.is_active = True
        cls.user.save()
        cls.obj = SimpleModel.objects.create(text="For admin logentry test")

    def test_auditlog_admin(self):
        self.client.login(username=self.username, password=self.password)
        log_pk = self.obj.history.latest().pk
        res = self.client.get("/admin/auditlog/logentry/")
        assert res.status_code == 200
        res = self.client.get("/admin/auditlog/logentry/add/")
        assert res.status_code == 200
        res = self.client.get(f"/admin/auditlog/logentry/{log_pk}/", follow=True)
        assert res.status_code == 200
        res = self.client.get(f"/admin/auditlog/logentry/{log_pk}/delete/")
        assert res.status_code == 200
        res = self.client.get(f"/admin/auditlog/logentry/{log_pk}/history/")
        assert res.status_code == 200


class NoDeleteHistoryTest(TestCase):
    def test_delete_related(self):
        instance = SimpleModel.objects.create(integer=1)
        assert LogEntry.objects.all().count() == 1
        instance.integer = 2
        instance.save()
        assert LogEntry.objects.all().count() == 2

        instance.delete()
        entries = LogEntry.objects.order_by("id")

        # The "DELETE" record is always retained
        assert LogEntry.objects.all().count() == 1
        assert entries.first().action == LogEntry.Action.DELETE

    def test_no_delete_related(self):
        instance = NoDeleteHistoryModel.objects.create(integer=1)
        self.assertEqual(LogEntry.objects.all().count(), 1)
        instance.integer = 2
        instance.save()
        self.assertEqual(LogEntry.objects.all().count(), 2)

        instance.delete()
        entries = LogEntry.objects.order_by("id")
        self.assertEqual(entries.count(), 3)
        self.assertEqual(
            list(entries.values_list("action", flat=True)),
            [LogEntry.Action.CREATE, LogEntry.Action.UPDATE, LogEntry.Action.DELETE],
        )
