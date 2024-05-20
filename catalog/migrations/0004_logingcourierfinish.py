# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-22 19:35
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('catalog', '0003_auto_20160303_1347'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogingCourierFinish',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430')),
                ('textlog', models.TextField(verbose_name='\u041b\u043e\u0433')),
                ('courier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='courier_logcourierfinish_set', to=settings.AUTH_USER_MODEL, verbose_name='\u041a\u0443\u0440\u044c\u0435\u0440')),
            ],
            options={
                'verbose_name': '\u041b\u043e\u0433 \u043f\u0440\u0438\u0435\u043c\u043a\u0438 \u043a\u0443\u0440\u044c\u0435\u0440\u0430',
                'verbose_name_plural': '\u041b\u043e\u0433 \u043f\u0440\u0438\u0435\u043c\u043a\u0438 \u043a\u0443\u0440\u044c\u0435\u0440\u0430',
                'permissions': (('courier', '\u041a\u0443\u0440\u044c\u0435\u0440 \u0437\u0430\u043a\u0430\u0437\u0430'),),
            },
        ),
    ]
