# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auditlog', '0003_logentry_remote_addr'),
    ]

    operations = [
        migrations.AddField(
            model_name='logentry',
            name='additional_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True, blank=True),
        ),
    ]
