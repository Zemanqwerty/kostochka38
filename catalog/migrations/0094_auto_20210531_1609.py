# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2021-05-31 16:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0093_auto_20210531_1100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tempzakaz',
            name='summ',
            field=models.FloatField(verbose_name='\u0421\u0443\u043c\u043c\u0430'),
        ),
    ]
