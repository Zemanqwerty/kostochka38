# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2021-06-08 15:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0011_new_action_target'),
    ]

    operations = [
        migrations.AlterField(
            model_name='new',
            name='action_target',
            field=models.PositiveSmallIntegerField(choices=[(0, '\u0412\u0435\u0437\u0434\u0435'), (1, '\u041e\u043d\u043b\u0430\u0439\u043d'), (2, '\u0420\u043e\u0437\u043d\u0438\u0446\u0430')], default=0, verbose_name='\u041e\u0431\u043b\u0430\u0441\u0442\u044c \u043f\u0440\u0438\u043c\u0435\u043d\u0435\u043d\u0438\u044f'),
        ),
    ]
