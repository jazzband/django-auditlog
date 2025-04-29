from django.test import TestCase, override_settings
from test_app.models import JSONModel, SimpleModel

from auditlog.registry import AuditlogModelRegistry


class JSONForChangesTest(TestCase):

    def setUp(self):
        self.test_auditlog = AuditlogModelRegistry()

    @override_settings(AUDITLOG_STORE_JSON_CHANGES=True)
    def test_use_json_for_changes_with_simplemodel(self):
        self.test_auditlog.register_from_settings()

        smm = SimpleModel()
        smm.save()
        changes_dict = smm.history.latest().changes_dict

        # compare the id, text, boolean and datetime fields
        id_field_changes = changes_dict["id"]
        self.assertIsNone(id_field_changes[0])
        self.assertIsInstance(
            id_field_changes[1], int
        )  # the id depends on state of the database

        text_field_changes = changes_dict["text"]
        self.assertEqual(text_field_changes, [None, ""])

        boolean_field_changes = changes_dict["boolean"]
        self.assertEqual(boolean_field_changes, [None, False])

        # datetime should be serialized to string
        datetime_field_changes = changes_dict["datetime"]
        self.assertIsNone(datetime_field_changes[0])
        self.assertIsInstance(datetime_field_changes[1], str)

    @override_settings(AUDITLOG_STORE_JSON_CHANGES=True)
    def test_use_json_for_changes_with_jsonmodel(self):
        self.test_auditlog.register_from_settings()

        json_model = JSONModel()
        json_model.json = {"test_key": "test_value"}
        json_model.save()
        changes_dict = json_model.history.latest().changes_dict

        id_field_changes = changes_dict["json"]
        self.assertEqual(id_field_changes, [None, {"test_key": "test_value"}])
