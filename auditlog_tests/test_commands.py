"""Tests for auditlog.management.commands"""

import datetime
from io import StringIO
from unittest import mock

import freezegun
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.test.utils import skipIf
from test_app.models import SimpleModel

from auditlog.management.commands.auditlogflush import TruncateQuery


class AuditlogFlushTest(TestCase):
    def setUp(self):
        input_patcher = mock.patch("builtins.input")
        self.mock_input = input_patcher.start()
        self.addCleanup(input_patcher.stop)

    def make_object(self):
        return SimpleModel.objects.create(text="I am a simple model.")

    def call_command(self, *args, **kwargs):
        outbuf = StringIO()
        errbuf = StringIO()
        call_command("auditlogflush", *args, stdout=outbuf, stderr=errbuf, **kwargs)
        return outbuf.getvalue().strip(), errbuf.getvalue().strip()

    def test_flush_yes(self):
        obj = self.make_object()
        self.assertEqual(obj.history.count(), 1, msg="There is one log entry.")

        out, err = self.call_command("--yes")

        self.assertEqual(obj.history.count(), 0, msg="There are no log entries.")
        self.assertEqual(
            out, "Deleted 1 objects.", msg="Output shows deleted 1 object."
        )
        self.assertEqual(err, "", msg="No stderr")

    def test_flush_no(self):
        obj = self.make_object()
        self.assertEqual(obj.history.count(), 1, msg="There is one log entry.")

        self.mock_input.return_value = "N\n"
        out, err = self.call_command()

        self.assertEqual(obj.history.count(), 1, msg="There is still one log entry.")
        self.assertEqual(
            out,
            "This action will clear all log entries from the database.\nAborted.",
            msg="Output shows warning and aborted.",
        )
        self.assertEqual(err, "", msg="No stderr")

    def test_flush_input_yes(self):
        obj = self.make_object()
        self.assertEqual(obj.history.count(), 1, msg="There is one log entry.")

        self.mock_input.return_value = "Y\n"
        out, err = self.call_command()

        self.assertEqual(obj.history.count(), 0, msg="There are no log entries.")
        self.assertEqual(
            out,
            "This action will clear all log entries from the database.\nDeleted 1 objects.",
            msg="Output shows warning and deleted 1 object.",
        )
        self.assertEqual(err, "", msg="No stderr")

    def test_before_date_input(self):
        self.mock_input.return_value = "N\n"
        out, err = self.call_command("--before-date=2000-01-01")
        self.assertEqual(
            out,
            (
                "This action will clear all log entries before "
                "2000-01-01 from the database.\nAborted."
            ),
            msg="Output shows warning with date and then aborted.",
        )
        self.assertEqual(err, "", msg="No stderr")

    def test_before_date(self):
        with freezegun.freeze_time("1999-12-31"):
            obj = self.make_object()

        with freezegun.freeze_time("2000-01-02"):
            obj.text = "I have new text"
            obj.save()

        self.assertEqual(
            {v["timestamp"] for v in obj.history.values("timestamp")},
            {
                datetime.datetime(1999, 12, 31, tzinfo=datetime.timezone.utc),
                datetime.datetime(2000, 1, 2, tzinfo=datetime.timezone.utc),
            },
            msg="Entries exist for 1999-12-31 and 2000-01-02",
        )

        out, err = self.call_command("--yes", "--before-date=2000-01-01")
        self.assertEqual(
            {v["timestamp"] for v in obj.history.values("timestamp")},
            {
                datetime.datetime(2000, 1, 2, tzinfo=datetime.timezone.utc),
            },
            msg="An entry exists only for 2000-01-02",
        )
        self.assertEqual(
            out, "Deleted 1 objects.", msg="Output shows deleted 1 object."
        )
        self.assertEqual(err, "", msg="No stderr")


class AuditlogFlushWithTruncateTest(TransactionTestCase):
    def setUp(self):
        input_patcher = mock.patch("builtins.input")
        self.mock_input = input_patcher.start()
        self.addCleanup(input_patcher.stop)

    def make_object(self):
        return SimpleModel.objects.create(text="I am a simple model.")

    def call_command(self, *args, **kwargs):
        outbuf = StringIO()
        errbuf = StringIO()
        call_command("auditlogflush", *args, stdout=outbuf, stderr=errbuf, **kwargs)
        return outbuf.getvalue().strip(), errbuf.getvalue().strip()

    def test_flush_with_both_truncate_and_before_date_options(self):
        obj = self.make_object()
        self.assertEqual(obj.history.count(), 1, msg="There is one log entry.")
        out, err = self.call_command("--truncate", "--before-date=2000-01-01")

        self.assertEqual(obj.history.count(), 1, msg="There is still one log entry.")
        self.assertEqual(
            out,
            "Truncate deletes all log entries and can not be passed with before-date.",
            msg="Output shows error",
        )
        self.assertEqual(err, "", msg="No stderr")

    @skipIf(
        not TruncateQuery.support_truncate_statement(connection.vendor),
        "Database does not support TRUNCATE",
    )
    def test_flush_with_truncate_and_yes(self):
        obj = self.make_object()
        self.assertEqual(obj.history.count(), 1, msg="There is one log entry.")
        out, err = self.call_command("--truncate", "--y")

        self.assertEqual(obj.history.count(), 0, msg="There is no log entry.")
        self.assertEqual(
            out,
            "Truncated log entry table.",
            msg="Output shows table gets truncate",
        )
        self.assertEqual(err, "", msg="No stderr")

    @skipIf(
        not TruncateQuery.support_truncate_statement(connection.vendor),
        "Database does not support TRUNCATE",
    )
    def test_flush_with_truncate_with_input_yes(self):
        obj = self.make_object()
        self.assertEqual(obj.history.count(), 1, msg="There is one log entry.")
        self.mock_input.return_value = "Y\n"
        out, err = self.call_command("--truncate")

        self.assertEqual(obj.history.count(), 0, msg="There is no log entry.")
        self.assertEqual(
            out,
            "This action will clear all log entries from the database.\nTruncated log entry table.",
            msg="Output shows warning and table gets truncate",
        )
        self.assertEqual(err, "", msg="No stderr")

    @mock.patch(
        "django.db.connection.vendor",
        new_callable=mock.PropertyMock(return_value="unknown"),
    )
    @mock.patch(
        "django.db.connection.display_name",
        new_callable=mock.PropertyMock(return_value="Unknown"),
    )
    def test_flush_with_truncate_for_unsupported_database_vendor(
        self, mocked_vendor, mocked_db_name
    ):
        obj = self.make_object()
        self.assertEqual(obj.history.count(), 1, msg="There is one log entry.")
        out, err = self.call_command("--truncate", "--y")

        self.assertEqual(obj.history.count(), 1, msg="There is still one log entry.")
        self.assertEqual(
            out,
            "Database Unknown does not support truncate statement.",
            msg="Output shows error",
        )
        self.assertEqual(err, "", msg="No stderr")
