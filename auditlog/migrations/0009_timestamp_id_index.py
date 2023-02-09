# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auditlog", "0008_timestamp_index"),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name="logentry",
            index_together={("timestamp", "id")},
        ),
        migrations.AlterField(
            model_name="logentry",
            name="timestamp",
            field=models.DateTimeField(auto_now_add=True, verbose_name="timestamp"),
        ),
    ]
