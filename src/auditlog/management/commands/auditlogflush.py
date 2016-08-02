from django.core.management.base import NoArgsCommand
from six import moves

from auditlog.models import LogEntry


class Command(NoArgsCommand):
    help = 'Deletes all log entries from the database.'

    def handle_noargs(self, **options):
        answer = None

        while answer not in ['', 'y', 'n']:
            answer = moves.input("Are you sure? [y/N]: ").lower().strip()

        if answer == 'y':
            count = LogEntry.objects.all().count()
            LogEntry.objects.all().delete()

            print("Deleted %d objects." % count)
