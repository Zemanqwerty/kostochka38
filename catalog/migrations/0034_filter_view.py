# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2019-01-12 00:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0033_auto_20190111_2236'),
    ]

    operations = [
        migrations.AddField(
            model_name='filter',
            name='view',
            field=models.PositiveIntegerField(default=0, verbose_name='\u041a\u043b\u0438\u043a\u0438'),
        ),
    ]
