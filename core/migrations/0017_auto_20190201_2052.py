# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2019-02-01 20:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20190201_2046'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='address_plat',
            field=models.CharField(blank=True, max_length=512, null=True, verbose_name='\u0410\u0434\u0440\u0435\u0441 \u041f\u043b\u0430\u0442\u0435\u043b\u044c\u0449\u0438\u043a\u0430'),
        ),
        migrations.AlterField(
            model_name='account',
            name='address_pol',
            field=models.CharField(blank=True, max_length=512, null=True, verbose_name='\u0410\u0434\u0440\u0435\u0441 \u0413\u0440\u0443\u0437\u043e\u043f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044f'),
        ),
    ]
