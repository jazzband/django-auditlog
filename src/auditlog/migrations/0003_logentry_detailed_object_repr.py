# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('auditlog', '0002_auto_support_long_primary_keys'),
    ]

    operations = [
        migrations.AddField(
            model_name='logentry',
            name='detailed_object_repr',
            field=jsonfield.fields.JSONField(null=True, blank=True),
        ),
    ]
