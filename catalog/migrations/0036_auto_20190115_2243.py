# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2019-01-15 22:43
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('catalog', '0035_itemavailabilitylog'),
    ]

    operations = [
        migrations.AddField(
            model_name='insidezakaz',
            name='manager',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='manager_insidezakaz_set', to=settings.AUTH_USER_MODEL, verbose_name='\u041c\u0435\u043d\u0435\u0434\u0436\u0435\u0440'),
        ),
        migrations.AlterField(
            model_name='zakaz',
            name='manager',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='manager_zakaz_set', to=settings.AUTH_USER_MODEL, verbose_name='\u041c\u0435\u043d\u0435\u0434\u0436\u0435\u0440'),
        ),
    ]
