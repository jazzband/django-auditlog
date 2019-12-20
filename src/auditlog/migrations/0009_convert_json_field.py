from django.db import migrations
from django.contrib.auth.management import create_permissions


def convert_json_field(apps, schema_editor):
    LogEntry = apps.get_model("auditlog", "LogEntry")

    for log_entry in LogEntry.objects.all():
        log_entry.additional_data_new = log_entry.additional_data  
        log_entry.save()


class Migration(migrations.Migration):

    dependencies = [("auditlog", "0008_logentry_additional_data_new")]

    operations = [
        migrations.RunPython(
            convert_json_field,
            reverse_code=migrations.RunPython.noop,
        )
    ]
