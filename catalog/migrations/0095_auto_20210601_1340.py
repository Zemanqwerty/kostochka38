# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2021-06-01 13:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0094_auto_20210531_1609'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='filtersitemaplink',
            name='description',
        ),
        migrations.RemoveField(
            model_name='filtersitemaplink',
            name='h1',
        ),
        migrations.RemoveField(
            model_name='filtersitemaplink',
            name='link',
        ),
        migrations.AddField(
            model_name='filtersitemaplink',
            name='filters',
            field=models.ManyToManyField(to='catalog.Filter'),
        ),
        migrations.AddField(
            model_name='filtersitemaplink',
            name='producer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='catalog.Producer'),
        ),
        migrations.AddField(
            model_name='filtersitemaplink',
            name='slug',
            field=models.CharField(max_length=512, null=True),
        )
    ]
