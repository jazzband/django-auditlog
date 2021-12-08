from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    help = "Deletes all log entries from the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "-y, --yes",
            action="store_true",
            default=None,
            help="Continue without asking confirmation.",
            dest="yes",
        )

    def handle(self, *args, **options):
        answer = options["yes"]

        if answer is None:
            self.stdout.write(
                "This action will clear all log entries from the database."
            )
            response = (
                input("Are you sure you want to continue? [y/N]: ").lower().strip()
            )
            answer = response == "y"

        if answer:
            with connections.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE auditlog_logentry;")
                self.stdout.write("Deleted all objects.")
        else:
            self.stdout.write("Aborted.")
