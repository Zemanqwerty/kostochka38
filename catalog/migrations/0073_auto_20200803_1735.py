# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2020-08-03 17:35
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0072_auto_20200803_1316'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movementofgoods',
            name='courier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='\u041a\u0443\u0440\u044c\u0435\u0440'),
        ),
        migrations.AlterField(
            model_name='movementofgoods',
            name='courier_paid',
            field=models.BooleanField(default=False, verbose_name='\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043e \u043a\u0443\u0440\u044c\u0435\u0440\u0443'),
        ),
    ]
