from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auditlog", "0016_add_actor_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="logentry",
            name="custom_data",
            field=models.JSONField(
                null=True, verbose_name="custom data", blank=True,
            ),
        ),
    ]
