from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auditlog", "0015_alter_logentry_changes"),
    ]

    operations = [
        migrations.AddField(
            model_name="logentry",
            name="remote_port",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="remote port"
            ),
        ),
    ]
