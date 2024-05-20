# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2019-10-06 16:55
from __future__ import unicode_literals

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_auto_20190703_2211'),
    ]

    operations = [
        migrations.AddField(
            model_name='slide',
            name='slide_image_mobile',
            field=models.ImageField(default=1, help_text='400x180', upload_to=core.models.get_file_path, verbose_name='\u0444\u043e\u043d \u043d\u0430 \u043c\u043e\u0431\u0438\u043b\u0435'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='slide',
            name='slide_image',
            field=models.ImageField(help_text='1600x400', upload_to=core.models.get_file_path, verbose_name='\u0444\u043e\u043d'),
        ),
    ]
