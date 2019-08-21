# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auditlog', '0007_object_pk_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logentry',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='timestamp'),
        ),
    ]
