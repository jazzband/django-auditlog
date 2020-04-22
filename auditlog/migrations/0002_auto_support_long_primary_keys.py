# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auditlog', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logentry',
            name='object_id',
            field=models.BigIntegerField(db_index=True, null=True, verbose_name='object id', blank=True),
        ),
    ]
