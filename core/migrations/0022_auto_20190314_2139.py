# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2019-03-14 21:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_auto_20190203_1717'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='optovik',
            field=models.BooleanField(default=False, verbose_name='\u041e\u043f\u0442\u043e\u0432\u0438\u043a'),
        ),
        migrations.AddField(
            model_name='account',
            name='zavodchik',
            field=models.BooleanField(default=False, verbose_name='\u0417\u0410\u0432\u043e\u0434\u0447\u0438\u043a/\u043f\u0438\u0442\u043e\u043c\u043d\u0438\u043a'),
        ),
        migrations.AlterField(
            model_name='account',
            name='okpo_plat',
            field=models.IntegerField(blank=True, null=True, verbose_name='\u041e\u041a\u041f\u041e \u041f\u043b\u0430\u0442\u0435\u043b\u044c\u0449\u0438\u043a\u0430'),
        ),
    ]
