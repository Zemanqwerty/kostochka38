# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2021-03-26 09:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0083_zakaz_target_sended'),
    ]

    operations = [
        migrations.AddField(
            model_name='filter',
            name='ceo_title',
            field=models.CharField(max_length=128, null=True, verbose_name='CEO \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435'),
        ),
    ]