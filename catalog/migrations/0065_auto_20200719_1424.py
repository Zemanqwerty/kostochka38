# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2020-07-19 14:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0064_auto_20200719_1423'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zakaz',
            name='summ',
            field=models.FloatField(default=0, verbose_name='\u0421\u0443\u043c\u043c\u0430 \u0437\u0430\u043a\u0430\u0437\u0430'),
        ),
    ]