# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2020-08-01 16:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0069_auto_20200801_1644'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zakaz',
            name='phone',
            field=models.CharField(blank=True, default=0, max_length=32, null=True, verbose_name='\u0422\u0435\u043b\u0435\u0444\u043e\u043d'),
        ),
    ]
