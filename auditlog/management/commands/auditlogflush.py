import datetime

from django.core.management.base import BaseCommand

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

    def handle(self, *args, **options):
        answer = options["yes"]
        before = options["before_date"]

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

        if answer:
            entries = LogEntry.objects.all()
            if before is not None:
                entries = entries.filter(timestamp__date__lt=before)
            count, _ = entries.delete()
            self.stdout.write("Deleted %d objects." % count)
        else:
            self.stdout.write("Aborted.")
