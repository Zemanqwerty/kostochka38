# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2020-08-04 12:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kassa', '0008_auto_20200720_1423'),
    ]

    operations = [
        migrations.CreateModel(
            name='Encashment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('money', models.IntegerField(verbose_name='\u041a\u043e\u043b-\u0432\u043e \u0434\u0435\u043d\u0435\u0433')),
                ('comment', models.TextField(verbose_name='\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('duty', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='kassa.Duty', verbose_name='\u0421\u043c\u0435\u043d\u0430')),
            ],
        ),
    ]
