# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2019-12-17 21:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0045_remove_producer_segment_new'),
    ]

    operations = [
        migrations.AddField(
            model_name='priceparser',
            name='result',
            field=models.TextField(blank=True, null=True, verbose_name='\u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442'),
        ),
    ]