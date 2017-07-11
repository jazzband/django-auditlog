# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from jsonfield_compat import JSONField


class Migration(migrations.Migration):

    dependencies = [
        ('auditlog', '0007_object_pk_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logentry',
            name='additional_data',
            field=JSONField(null=True, verbose_name='additional data', blank=True),
        ),
    ]
