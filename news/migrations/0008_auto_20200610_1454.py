# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2020-06-10 14:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0007_new_discount_size'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='new',
            options={'ordering': ['order'], 'verbose_name': '\u041d\u043e\u0432\u043e\u0441\u0442\u044c/\u0410\u043a\u0446\u0438\u044f', 'verbose_name_plural': '\u041d\u043e\u0432\u043e\u0441\u0442\u0438/\u0410\u043a\u0446\u0438\u0438'},
        ),
        migrations.AddField(
            model_name='new',
            name='order',
            field=models.PositiveIntegerField(default=9999, verbose_name='\u041f\u043e\u0440\u044f\u0434\u043e\u043a'),
        ),
    ]
