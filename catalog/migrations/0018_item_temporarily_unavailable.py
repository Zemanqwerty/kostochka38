# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-24 17:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0017_auto_20161126_1957'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='temporarily_unavailable',
            field=models.BooleanField(default=False, verbose_name='\u0412\u0440\u0435\u043c\u0435\u043d\u043d\u043e \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d'),
        ),
    ]
