# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2018-06-22 18:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0030_auto_20180616_1926'),
    ]

    operations = [
        migrations.AddField(
            model_name='zakaz',
            name='f_fiscal_data',
            field=models.TextField(blank=True, null=True, verbose_name='\u0424-data'),
        ),
        migrations.AddField(
            model_name='zakaz',
            name='f_id',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='\u0424-ID \u0437\u0430\u0434\u0430\u0447\u0438'),
        ),
        migrations.AddField(
            model_name='zakaz',
            name='f_print',
            field=models.BooleanField(default=False, verbose_name='\u0424-\u041f\u0435\u0447\u0430\u0442\u044c'),
        ),
        migrations.AddField(
            model_name='zakaz',
            name='f_state',
            field=models.IntegerField(blank=True, choices=[(1, '\u041e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e \u043d\u0430 \u0424\u0420'), (2, '\u041e\u041a'), (3, '\u041e\u0448\u0438\u0431\u043a\u0430')], null=True, verbose_name='\u0424-\u0421\u0442\u0430\u0442\u0443\u0441'),
        ),
    ]
