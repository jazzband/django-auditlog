from django.db import migrations
from django_jsonfield_backport.models import JSONField


class Migration(migrations.Migration):

    dependencies = [
        ("auditlog", "0008_action_index"),
    ]

    operations = [
        migrations.AlterField(
            model_name="logentry",
            name="additional_data",
            field=JSONField(blank=True, null=True, verbose_name="additional data"),
        ),
    ]
