# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-13 20:40
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='new',
            name='exp_date',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2016, 12, 13, 20, 40, 18, 12917), null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0438\u044f'),
        ),
    ]
