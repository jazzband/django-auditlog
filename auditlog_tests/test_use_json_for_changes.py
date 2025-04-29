from django.test import TestCase, override_settings
from test_app.models import JSONModel, RelatedModel, SimpleModel

from auditlog.registry import AuditlogModelRegistry


class JSONForChangesTest(TestCase):

    def setUp(self):
        self.test_auditlog = AuditlogModelRegistry()

    @override_settings(AUDITLOG_STORE_JSON_CHANGES="str")
    def test_wrong_setting_type(self):
        with self.assertRaisesMessage(
            TypeError, "Setting 'AUDITLOG_STORE_JSON_CHANGES' must be a boolean"
        ):
            self.test_auditlog.register_from_settings()

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

    @override_settings(AUDITLOG_STORE_JSON_CHANGES=True)
    def test_use_json_for_changes_with_jsonmodel_with_empty_list(self):
        self.test_auditlog.register_from_settings()

        json_model = JSONModel()
        json_model.json = []
        json_model.save()
        changes_dict = json_model.history.latest().changes_dict

        id_field_changes = changes_dict["json"]
        self.assertEqual(id_field_changes, [None, []])

    @override_settings(AUDITLOG_STORE_JSON_CHANGES=True)
    def test_use_json_for_changes_with_jsonmodel_with_complex_data(self):
        self.test_auditlog.register_from_settings()

        json_model = JSONModel()
        json_model.json = {
            "key": "test_value",
            "key_dict": {"inner_key": "inner_value"},
            "key_tuple": ("item1", "item2", "item3"),
        }
        json_model.save()
        changes_dict = json_model.history.latest().changes_dict

        id_field_changes = changes_dict["json"]
        self.assertEqual(
            id_field_changes,
            [
                None,
                {
                    "key": "test_value",
                    "key_dict": {"inner_key": "inner_value"},
                    "key_tuple": [
                        "item1",
                        "item2",
                        "item3",
                    ],  # tuple is converted to list, that's ok
                },
            ],
        )

    @override_settings(AUDITLOG_STORE_JSON_CHANGES=True)
    def test_use_json_for_changes_with_jsonmodel_with_related_model(self):
        self.test_auditlog.register_from_settings()

        simple = SimpleModel.objects.create()
        one_simple = SimpleModel.objects.create()
        related_model = RelatedModel.objects.create(
            one_to_one=simple, related=one_simple
        )
        related_model.save()
        changes_dict = related_model.history.latest().changes_dict

        field_related_changes = changes_dict["related"]
        self.assertEqual(field_related_changes, [None, one_simple.id])

        field_one_to_one_changes = changes_dict["one_to_one"]
        self.assertEqual(field_one_to_one_changes, [None, simple.id])
