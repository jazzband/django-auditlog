from django.db import migrations, models
from django_jsonfield_backport.models import JSONField


class Migration(migrations.Migration):

    dependencies = [
        ("auditlog", "0004_logentry_detailed_object_repr"),
    ]

    operations = [
        migrations.AlterField(
            model_name="logentry",
            name="additional_data",
            field=JSONField(null=True, verbose_name="additional data", blank=True),
        ),
    ]
