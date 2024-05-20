# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2020-03-26 21:17
from __future__ import unicode_literals

import catalog.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0050_logingcourierfinish_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='zakaz',
            name='inbox',
            field=models.BooleanField(default=False, verbose_name='\u0423\u043f\u0430\u043a\u043e\u0432\u0430\u0442\u044c \u0434\u043b\u044f \u043e\u0442\u043f\u0440\u0430\u0432\u043a\u0438'),
        ),
        migrations.AlterField(
            model_name='logingcourierfinish',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=catalog.models.get_file_path, verbose_name='\u0421\u043a\u0440\u0438\u043d'),
        ),
    ]
