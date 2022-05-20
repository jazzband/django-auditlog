from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auditlog", "0004_logentry_detailed_object_repr"),
    ]

    operations = [
        migrations.AlterField(
            model_name="logentry",
            name="additional_data",
            field=models.JSONField(
                null=True, verbose_name="additional data", blank=True
            ),
        ),
    ]
