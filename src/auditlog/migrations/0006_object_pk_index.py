# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auditlog', '0005_logentry_additional_data_verbose_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logentry',
            name='object_pk',
            field=models.CharField(verbose_name='object pk', db_index=True, max_length=255),
        ),
    ]
