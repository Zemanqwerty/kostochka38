# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-07-11 23:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0008_auto_20160711_2240'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autozakaz',
            name='zakaz',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalog.Zakaz', verbose_name='\u0420\u043e\u0434\u0438\u0442\u0435\u043b\u044c\u0441\u043a\u0438\u0439 \u0437\u0430\u043a\u0430\u0437'),
        ),
    ]
