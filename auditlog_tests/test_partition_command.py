"""
Tests for the auditlogpartition management command.
"""

from io import StringIO
from unittest import mock, skipIf

import freezegun
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.db.models import Max
from django.test import TransactionTestCase
from test_app.models import SimpleModel

from auditlog.management.commands.auditlogpartition import Command
from auditlog.models import LogEntry


def _table_name() -> str:
    return LogEntry._meta.db_table


@skipIf(settings.TEST_DB_BACKEND != "postgresql", "PostgreSQL-specific test")
class AuditlogPartitionCommandTest(TransactionTestCase):
    databases = "__all__"

    def setUp(self):
        super().setUp()
        self._reset_schema()

    def tearDown(self):
        self._reset_schema()
        super().tearDown()

    def _reset_schema(self):
        call_command("migrate", "auditlog", "zero", verbosity=0, database="default")
        call_command("migrate", "auditlog", verbosity=0, database="default")

    def _call_partition(self, *args: str) -> str:
        out = StringIO()
        call_command(
            "auditlogpartition",
            *args,
            stdout=out,
            stderr=StringIO(),
        )
        return out.getvalue()

    def _is_partitioned(self) -> bool:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM pg_partitioned_table WHERE partrelid = %s::regclass);",
                [_table_name()],
            )
            return cursor.fetchone()[0]

    def _partition_suffixes(self) -> set[str]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    child.relname
                FROM pg_inherits
                JOIN pg_class parent ON parent.oid = pg_inherits.inhparent
                JOIN pg_class child ON child.oid = pg_inherits.inhrelid
                WHERE parent.oid = %s::regclass
                ORDER BY child.relname;
                """,
                [_table_name()],
            )
            names = [row[0] for row in cursor.fetchall()]
        suffixes = set()
        for name in names:
            suffix = name.split("_")[-2:]
            suffixes.add("_".join(suffix))
        return suffixes

    def _ensure_partitioned(self):
        if not self._is_partitioned():
            with freezegun.freeze_time("2025-11-15"):
                self._call_partition("init", "--ahead=0")

    def test_init_safe_creates_partitions(self):
        with freezegun.freeze_time("2025-11-15"):
            out = self._call_partition("init", "--ahead=1")

        self.assertIn("Partitioning initialized successfully.", out)
        self.assertTrue(self._is_partitioned())
        suffixes = self._partition_suffixes()
        self.assertIn("2025_11", suffixes)
        self.assertIn("2025_12", suffixes)

    def test_init_convert_moves_rows(self):
        with freezegun.freeze_time("2025-01-12"):
            SimpleModel.objects.create(text="first")
        with freezegun.freeze_time("2025-03-18"):
            obj = SimpleModel.objects.first()
            obj.text = "updated"
            obj.save()

        initial_count = LogEntry.objects.count()
        original_copy = Command._copy_table_to_shadow

        def patched_copy(self, *args, **kwargs):
            result = original_copy(self, *args, **kwargs)
            with freezegun.freeze_time("2025-03-20"):
                SimpleModel.objects.create(text="late convert")
            return result

        with (
            freezegun.freeze_time("2025-04-01"),
            mock.patch.object(Command, "_copy_table_to_shadow", patched_copy),
        ):
            self._call_partition("init", "--convert", "--ahead=0")

        self.assertTrue(self._is_partitioned())
        self.assertEqual(LogEntry.objects.count(), initial_count + 1)

        late_instance = SimpleModel.objects.get(text="late convert")
        self.assertEqual(late_instance.history.count(), 1)

        suffixes = self._partition_suffixes()
        self.assertIn("2025_01", suffixes)
        self.assertIn("2025_03", suffixes)

        max_id = LogEntry.objects.aggregate(max_id=Max("id"))["max_id"]
        with freezegun.freeze_time("2025-04-05"):
            SimpleModel.objects.create(text="another")
        new_max = LogEntry.objects.aggregate(max_id=Max("id"))["max_id"]
        self.assertGreater(new_max, max_id)
        self.assertEqual(LogEntry.objects.count(), initial_count + 2)

    def test_create_adds_future_partitions(self):
        self._ensure_partitioned()
        with freezegun.freeze_time("2025-11-15"):
            before = self._partition_suffixes()
            self._call_partition("create", "--start=2026-01", "--ahead=2")
            after = self._partition_suffixes()

        self.assertTrue({"2026_01", "2026_02", "2026_03"}.issubset(after))
        self.assertLessEqual(before, after)

    def test_prune_drops_old_partitions(self):
        self._ensure_partitioned()
        with freezegun.freeze_time("2024-01-15"):
            self._call_partition("create", "--start=2023-10", "--ahead=0")
        with freezegun.freeze_time("2025-11-15"):
            suffixes_before = self._partition_suffixes()
            self.assertIn("2023_10", suffixes_before)
            self._call_partition("prune", "--retention-months=6")
            suffixes_after = self._partition_suffixes()

        self.assertNotIn("2023_10", suffixes_after)

    def test_status_outputs_summary(self):
        self._ensure_partitioned()
        out = self._call_partition("status")
        self.assertIn("Partitioned: yes", out)
        self.assertIn("auditlog_logentry_", out)
