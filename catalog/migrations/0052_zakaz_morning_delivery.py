# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2020-04-04 18:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0051_auto_20200326_2117'),
    ]

    operations = [
        migrations.AddField(
            model_name='zakaz',
            name='morning_delivery',
            field=models.BooleanField(default=False, help_text='\u0413\u0430\u043b\u043a\u0430 \u0441\u0442\u0430\u0432\u0438\u0442\u0441\u044f, \u0435\u0441\u043b\u0438 \u0437\u0430\u043a\u0430\u0437 \u043d\u0435\u043e\u0431\u0445\u043e\u0434\u0438\u043c\u043e \u0437\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c "\u0441\u0435\u0433\u043e\u0434\u043d\u044f", \u0430 \u0434\u043e\u0441\u0442\u0430\u0432\u0438\u0442\u044c "\u0437\u0430\u0432\u0442\u0440\u0430"', verbose_name='\u0423\u0442\u0440\u0435\u043d\u043d\u044f\u044f \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0430'),
        ),
    ]
