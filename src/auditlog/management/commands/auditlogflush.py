from django.core.management.base import BaseCommand
from django.template.defaultfilters import pluralize

from auditlog.models import LogEntry


class Command(BaseCommand):
    help = 'Deletes all log entries from the database.'

    def handle(self, *args, **options):
        answer = None

        while answer not in ['', 'y', 'n']:
            answer = input('Are you sure? [y/N]: ').lower().strip()

        if answer == 'y':
            count = LogEntry.objects.all().count()
            LogEntry.objects.all().delete()

            print(f'Deleted {count} object{pluralize(count)}.')
