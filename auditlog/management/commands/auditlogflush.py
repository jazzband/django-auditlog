from django.core.management.base import BaseCommand

from auditlog.models import LogEntry


class Command(BaseCommand):
    help = "Deletes all log entries from the database."

    def add_arguments(self, parser):
        parser.add_argument('-y, --yes', action='store_true', default=None,
                            help="Continue without asking confirmation.", dest='yes')

    def handle(self, *args, **options):
        answer = options['yes']

        while answer is None:
            print("This action will clear all log entries from the database.")
            response = input("Are you sure you want to continue? [y/N]: ").lower().strip()
            answer = True if response == 'y' else False if response == 'n' else None

        if answer:
            count, _ = LogEntry.objects.all().delete()
            print("Deleted %d objects." % count)
        else:
            print("Aborted.")
