# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2022-10-10 14:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0104_auto_20220528_1409'),
    ]

    operations = [
        migrations.AddField(
            model_name='zakaz',
            name='f_taxtype',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='\u0422\u0438\u043f \u043d\u0430\u043b\u043e\u0433\u0430'),
        ),
    ]