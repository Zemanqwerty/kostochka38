# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2020-08-06 22:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0074_zakaz_f_response'),
    ]

    operations = [
        migrations.AddField(
            model_name='zakaz',
            name='ordered',
            field=models.BooleanField(default=False, verbose_name='\u041e\u0431\u0440\u0430\u0431\u043e\u0442\u0430\u043d\u043e \u0432 \u0430\u0432\u0442\u043e\u0441\u0431\u043e\u0440\u043a\u0435'),
        ),
    ]