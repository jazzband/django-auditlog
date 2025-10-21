from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("auditlog", "0018_logentry_remote_port"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="logentry",
            new_name="auditlog_timestamp_id_idx",
            old_fields=("timestamp", "id"),
        ),
    ]
