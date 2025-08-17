"""
PostgreSQL-specific tests for django-auditlog.
"""

from unittest import skipIf

from django.conf import settings
from django.test import TestCase
from test_app.models import PostgresArrayFieldModel


@skipIf(settings.TEST_DB_BACKEND != "postgresql", "PostgreSQL-specific test")
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
        self.assertEqual(
            self.latest_array_change,
            "Red, Green",
            msg="The human readable text for the two choices, 'Red, Green' is displayed.",
        )
        self.obj.arrayfield = [PostgresArrayFieldModel.GREEN]
        self.obj.save()
        self.assertEqual(
            self.latest_array_change,
            "Green",
            msg="The human readable text 'Green' is displayed.",
        )
        self.obj.arrayfield = []
        self.obj.save()
        self.assertEqual(
            self.latest_array_change,
            "",
            msg="The human readable text '' is displayed.",
        )
        self.obj.arrayfield = [PostgresArrayFieldModel.GREEN]
        self.obj.save()
        self.assertEqual(
            self.latest_array_change,
            "Green",
            msg="The human readable text 'Green' is displayed.",
        )
