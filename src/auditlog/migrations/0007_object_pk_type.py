# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auditlog', '0006_object_pk_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logentry',
            name='object_pk',
            field=models.CharField(verbose_name='object pk', max_length=255, db_index=True),
        ),
    ]
