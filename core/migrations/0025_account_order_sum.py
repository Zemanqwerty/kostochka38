# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2019-12-02 15:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_auto_20191006_1655'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='order_sum',
            field=models.IntegerField(blank=True, null=True, verbose_name='\u0421\u0443\u043c\u043c\u0430 \u0437\u0430\u043a\u0430\u0437\u043e\u0432'),
        ),
    ]
