# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2022-05-12 09:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_auto_20210826_1014'),
    ]

    operations = [
        migrations.AlterField(
            model_name='slide',
            name='expdate',
            field=models.DateTimeField(verbose_name='\u0413\u043e\u0434\u0435\u043d \u0434\u043e'),
        ),
        migrations.AlterField(
            model_name='slide',
            name='startdate',
            field=models.DateTimeField(verbose_name='\u0414\u0430\u0442\u0430 \u0437\u0430\u043f\u0443\u0441\u043a\u0430'),
        ),
    ]
