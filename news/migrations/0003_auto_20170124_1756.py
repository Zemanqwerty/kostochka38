# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-24 17:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0002_new_exp_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='new',
            name='exp_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0438\u044f'),
        ),
    ]
