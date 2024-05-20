# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2021-05-22 19:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_account_order_sum'),
    ]

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(verbose_name='\u0410\u043a\u0442\u0438\u0432\u043d\u043e')),
                ('text', models.TextField(verbose_name='\u0422\u0435\u043a\u0441\u0442')),
                ('hash', models.CharField(max_length=32, verbose_name=b'\xd0\xa5\xd0\xb5\xd1\x88 \xd1\x82\xd0\xb5\xd0\xba\xd1\x81\xd1\x82\xd0\xb0')),
            ],
            options={
                'verbose_name': '\u043e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u0435',
                'verbose_name_plural': '\u041e\u0431\u044a\u044f\u0432\u043b\u0435\u043d\u0438\u044f',
            },
        ),
    ]