from django.db import migrations, models
from django.utils.version import get_complete_version

if get_complete_version() >= (3, 1):
    from django.db.models import JSONField
else:
    from jsonfield.fields import JSONField


class Migration(migrations.Migration):

    dependencies = [
        ("auditlog", "0003_logentry_remote_addr"),
    ]

    operations = [
        migrations.AddField(
            model_name="logentry",
            name="additional_data",
            field=JSONField(null=True, blank=True),
        ),
    ]
