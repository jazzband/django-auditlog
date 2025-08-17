import datetime

from django.core.management.base import BaseCommand
from django.db import connection

from auditlog.models import LogEntry


class Command(BaseCommand):
    help = "Deletes all log entries from the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "-y",
            "--yes",
            action="store_true",
            default=None,
            help="Continue without asking confirmation.",
            dest="yes",
        )
        parser.add_argument(
            "-b",
            "--before-date",
            default=None,
            help="Flush all entries with a timestamp before a given date (ISO 8601).",
            dest="before_date",
            type=datetime.date.fromisoformat,
        )
        parser.add_argument(
            "-t",
            "--truncate",
            action="store_true",
            default=None,
            help="Truncate log entry table.",
            dest="truncate",
        )

    def handle(self, *args, **options):
        answer = options["yes"]
        truncate = options["truncate"]
        before = options["before_date"]
        if truncate and before:
            self.stdout.write(
                "Truncate deletes all log entries and can not be passed with before-date."
            )
            return
        if answer is None:
            warning_message = (
                "This action will clear all log entries from the database."
            )
            if before is not None:
                warning_message = f"This action will clear all log entries before {before} from the database."
            self.stdout.write(warning_message)
            response = (
                input("Are you sure you want to continue? [y/N]: ").lower().strip()
            )
            answer = response == "y"

        if not answer:
            self.stdout.write("Aborted.")
            return

        if not truncate:
            entries = LogEntry.objects.all()
            if before is not None:
                entries = entries.filter(timestamp__date__lt=before)
            count, _ = entries.delete()
            self.stdout.write("Deleted %d objects." % count)
        else:
            database_vendor = connection.vendor
            database_display_name = connection.display_name
            table_name = LogEntry._meta.db_table
            if not TruncateQuery.support_truncate_statement(database_vendor):
                self.stdout.write(
                    "Database %s does not support truncate statement."
                    % database_display_name
                )
                return
            with connection.cursor() as cursor:
                query = TruncateQuery.to_sql(table_name)
                cursor.execute(query)
            self.stdout.write("Truncated log entry table.")


class TruncateQuery:
    SUPPORTED_VENDORS = ("postgresql", "mysql", "oracle", "microsoft")

    @classmethod
    def support_truncate_statement(cls, database_vendor) -> bool:
        return database_vendor in cls.SUPPORTED_VENDORS

    @staticmethod
    def to_sql(table_name) -> str:
        return f"TRUNCATE TABLE {table_name};"
