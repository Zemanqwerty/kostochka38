# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2019-02-02 19:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_auto_20190202_1938'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='ur_lico',
            field=models.BooleanField(default=False, verbose_name='\u042e\u0440\u0438\u0434\u0438\u0447\u0435\u0441\u043a\u043e\u0435 \u043b\u0438\u0446\u043e'),
        ),
    ]