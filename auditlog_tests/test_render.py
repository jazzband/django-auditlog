from django.test import TestCase
from test_app.models import SimpleModel

from auditlog.models import LogEntry
from auditlog.templatetags.auditlog_tags import render_logentry_changes_html


class RenderChangesTest(TestCase):

    def _create_log_entry(self, action, changes):
        return LogEntry.objects.log_create(
            SimpleModel.objects.create(),
            action=action,
            changes=changes,
        )

    def test_render_changes_empty(self):
        log_entry = self._create_log_entry(LogEntry.Action.CREATE, {})
        result = render_logentry_changes_html(log_entry)
        self.assertEqual(result, "")

    def test_render_changes_simple_field(self):
        changes = {"text": ["old text", "new text"]}
        log_entry = self._create_log_entry(LogEntry.Action.UPDATE, changes)

        result = render_logentry_changes_html(log_entry)

        self.assertIn("<table>", result)
        self.assertIn("<th>#</th>", result)
        self.assertIn("<th>Field</th>", result)
        self.assertIn("<th>From</th>", result)
        self.assertIn("<th>To</th>", result)
        self.assertIn("old text", result)
        self.assertIn("new text", result)
        self.assertIsInstance(result, str)

    def test_render_changes_password_field(self):
        changes = {"password": ["oldpass", "newpass"]}
        log_entry = self._create_log_entry(LogEntry.Action.UPDATE, changes)

        result = render_logentry_changes_html(log_entry)

        self.assertIn("***", result)
        self.assertNotIn("oldpass", result)
        self.assertNotIn("newpass", result)

    def test_render_changes_m2m_field(self):
        changes = {
            "related_objects": {
                "type": "m2m",
                "operation": "add",
                "objects": ["obj1", "obj2", "obj3"],
            }
        }
        log_entry = self._create_log_entry(LogEntry.Action.UPDATE, changes)

        result = render_logentry_changes_html(log_entry)

        self.assertIn("<table>", result)
        self.assertIn("<th>#</th>", result)
        self.assertIn("<th>Relationship</th>", result)
        self.assertIn("<th>Action</th>", result)
        self.assertIn("<th>Objects</th>", result)
        self.assertIn("add", result)
        self.assertIn("obj1", result)
        self.assertIn("obj2", result)
        self.assertIn("obj3", result)

    def test_render_changes_mixed_fields(self):
        changes = {
            "text": ["old text", "new text"],
            "related_objects": {
                "type": "m2m",
                "operation": "remove",
                "objects": ["obj1"],
            },
        }
        log_entry = self._create_log_entry(LogEntry.Action.UPDATE, changes)

        result = render_logentry_changes_html(log_entry)

        tables = result.count("<table>")
        self.assertEqual(tables, 2)

        self.assertIn("old text", result)
        self.assertIn("new text", result)

        self.assertIn("remove", result)
        self.assertIn("obj1", result)

    def test_render_changes_field_verbose_name(self):
        changes = {"text": ["old", "new"]}
        log_entry = self._create_log_entry(LogEntry.Action.UPDATE, changes)

        result = render_logentry_changes_html(log_entry)

        self.assertIn("Text", result)

    def test_render_changes_with_none_values(self):
        changes = {"text": [None, "new text"], "boolean": [True, None]}
        log_entry = self._create_log_entry(LogEntry.Action.UPDATE, changes)

        result = render_logentry_changes_html(log_entry)

        self.assertIn("None", result)
        self.assertIn("new text", result)
        self.assertIn("True", result)

    def test_render_changes_sorted_fields(self):
        changes = {
            "z_field": ["old", "new"],
            "a_field": ["old", "new"],
            "m_field": ["old", "new"],
        }
        log_entry = self._create_log_entry(LogEntry.Action.UPDATE, changes)

        result = render_logentry_changes_html(log_entry)

        a_index = result.find("A field")
        m_index = result.find("M field")
        z_index = result.find("Z field")

        self.assertLess(a_index, m_index)
        self.assertLess(m_index, z_index)

    def test_render_changes_m2m_sorted_fields(self):
        changes = {
            "z_related": {"type": "m2m", "operation": "add", "objects": ["obj1"]},
            "a_related": {"type": "m2m", "operation": "remove", "objects": ["obj2"]},
        }
        log_entry = self._create_log_entry(LogEntry.Action.UPDATE, changes)

        result = render_logentry_changes_html(log_entry)

        a_index = result.find("A related")
        z_index = result.find("Z related")

        self.assertLess(a_index, z_index)

    def test_render_changes_create_action(self):
        changes = {
            "text": [None, "new value"],
            "boolean": [None, True],
        }
        log_entry = self._create_log_entry(LogEntry.Action.CREATE, changes)

        result = render_logentry_changes_html(log_entry)

        self.assertIn("<table>", result)
        self.assertIn("new value", result)
        self.assertIn("True", result)

    def test_render_changes_delete_action(self):
        changes = {
            "text": ["old value", None],
            "boolean": [True, None],
        }
        log_entry = self._create_log_entry(LogEntry.Action.DELETE, changes)

        result = render_logentry_changes_html(log_entry)

        self.assertIn("<table>", result)
        self.assertIn("old value", result)
        self.assertIn("True", result)
        self.assertIn("None", result)
