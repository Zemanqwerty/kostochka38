# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2018-06-28 17:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0031_auto_20180622_1858'),
    ]

    operations = [
        migrations.AddField(
            model_name='zakaz',
            name='f_check',
            field=models.BooleanField(default=True, verbose_name='\u0424-\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0447\u0435\u043a'),
        ),
    ]
