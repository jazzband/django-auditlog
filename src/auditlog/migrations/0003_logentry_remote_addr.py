# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auditlog', '0002_auto_support_long_primary_keys'),
    ]

    operations = [
        migrations.AddField(
            model_name='logentry',
            name='remote_addr',
            field=models.GenericIPAddressField(null=True, verbose_name='remote address', blank=True),
        ),
    ]
