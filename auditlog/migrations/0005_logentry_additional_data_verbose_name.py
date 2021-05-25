from django.db import migrations, models
from django.utils.version import get_complete_version

if get_complete_version() >= (3, 1):
    from django.db.models import JSONField
else:
    from jsonfield.fields import JSONField


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
