# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2019-10-17 18:37
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0044_auto_20191016_1108'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='producer',
            name='segment_new',
        ),
    ]