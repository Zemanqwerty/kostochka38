# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-22 19:35
from __future__ import unicode_literals

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20160303_1641'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='original_image',
            field=models.ImageField(upload_to=core.models.get_file_path),
        ),
    ]
