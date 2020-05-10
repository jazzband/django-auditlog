# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auditlog', '0007_object_pk_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logentry',
            name='action',
            field=models.PositiveSmallIntegerField(verbose_name='action', choices=[(0, 'create'), (1, 'update'), (2, 'delete'), (3, 'added')]),
        ),
    ]
