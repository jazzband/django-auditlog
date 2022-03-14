"""Tests for auditlog.management.commands"""

import datetime
from io import StringIO
from unittest import mock

import freezegun
from django.core.management import call_command
from django.test import TestCase

from auditlog_tests.models import SimpleModel


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
            "This action will clear all log entries before 2000-01-01 from the database.\nAborted.",
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
