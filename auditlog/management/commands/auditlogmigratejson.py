from math import ceil

from django.conf import settings
from django.core.management.base import BaseCommand

from auditlog.models import LogEntry


class Command(BaseCommand):
    help = "Migrates changes from changes_text to json changes."

    def add_arguments(self, parser):
        parser.add_argument(
            "-d",
            "--database",
            default=None,
            help="If provided, the script will use native db operations. "
            "Otherwise, it will use LogEntry.objects.bulk_create",
            dest="db",
            type=str,
            choices=["postgres", "mysql", "oracle"],
        )
        parser.add_argument(
            "-b",
            "--bactch-size",
            default=500,
            help="Split the migration into multiple batches. If 0, then no batching will be done. "
            "When passing a -d/database, the batch value will be ignored.",
            dest="batch_size",
            type=int,
        )

    def handle(self, *args, **options):
        database = options["db"]
        batch_size = options["batch_size"]

        if not self.check_logs():
            return

        if database:
            result = self.migrate_using_sql(database)
            self.stdout.write(
                f"Updated {result} records using native database operations."
            )
        else:
            result = self.migrate_using_django(batch_size)
            self.stdout.write(f"Updated {result} records using django operations.")

        self.check_logs()

    def check_logs(self):
        count = self.get_logs().count()
        if count:
            self.stdout.write(f"There are {count} records that needs migration.")
            return True

        self.stdout.write("All records are have been migrated.")
        if settings.AUDITLOG_USE_TEXT_CHANGES_IF_JSON_IS_NOT_PRESENT:
            self.stdout.write(
                "You can now set AUDITLOG_USE_TEXT_CHANGES_IF_JSON_IS_NOT_PRESENT to False."
            )

        return False

    def get_logs(self):
        return LogEntry.objects.filter(
            changes_text__isnull=False, changes__isnull=True
        ).exclude(changes_text__exact="")

    def migrate_using_django(self, batch_size):
        def _apply_django_migration(_logs) -> int:
            import json

            updated = []
            for log in _logs:
                try:
                    log.changes = json.loads(log.changes_text)
                except ValueError:
                    self.stderr.write(
                        f"ValueError was raised while migrating the log with id {log.id}."
                    )
                else:
                    updated.append(log)

            LogEntry.objects.bulk_update(updated, fields=["changes"])
            return len(updated)

        logs = self.get_logs()

        if not batch_size:
            return _apply_django_migration(logs)

        total_updated = 0
        for _ in range(ceil(logs.count() / batch_size)):
            total_updated += _apply_django_migration(self.get_logs()[:batch_size])
        return total_updated

    def migrate_using_sql(self, database):
        from django.db import connection

        def postgres():
            with connection.cursor() as cursor:
                cursor.execute(
                    'UPDATE auditlog_logentry SET changes="changes_text"::jsonb'
                )
                return cursor.cursor.rowcount

        if database == "postgres":
            return postgres()
        else:
            self.stderr.write(
                "Not yet implemented. Run this management command without passing a -d/--database argument."
            )
            return 0
