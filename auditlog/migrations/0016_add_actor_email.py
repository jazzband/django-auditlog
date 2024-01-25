from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auditlog", "0015_alter_logentry_changes"),
    ]

    operations = [
        migrations.AddField(
            model_name="logentry",
            name="actor_email",
            field=models.CharField(
                null=True, verbose_name="actor email", blank=True, max_length=254,
            ),
        ),
    ]
