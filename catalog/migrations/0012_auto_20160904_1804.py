# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-09-04 18:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0011_ordersort'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordersort',
            name='date',
            field=models.DateField(auto_now_add=True),
        ),
    ]
