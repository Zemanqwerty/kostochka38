# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2020-08-20 14:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0080_auto_20200812_1759'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='barcode',
            field=models.TextField(default=b'', verbose_name='\u0428\u0442\u0440\u0438\u0445\u043a\u043e\u0434'),
        ),
    ]
