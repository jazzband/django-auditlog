from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auditlog", "0008_action_index"),
    ]

    operations = [
        migrations.AlterField(
            model_name="logentry",
            name="additional_data",
            field=models.JSONField(
                blank=True, null=True, verbose_name="additional data"
            ),
        ),
    ]
