# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-07-12 16:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0009_auto_20160711_2343'),
    ]

    operations = [
        migrations.AddField(
            model_name='zakaz',
            name='autocreate',
            field=models.BooleanField(default=False, verbose_name='\u0410\u0432\u0442\u043e\u0441\u043e\u0437\u0434\u0430\u043d\u0438\u0435'),
        ),
    ]