# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2020-08-12 11:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kassa', '0010_auto_20200811_1608'),
    ]

    operations = [
        migrations.AddField(
            model_name='duty',
            name='cash_earned',
            field=models.FloatField(blank=True, null=True, verbose_name='\u041f\u0440\u043e\u0434\u0430\u043d\u043e \u0437\u0430 \u043d\u0430\u043b\u0438\u0447\u043a\u0443'),
        ),
    ]
