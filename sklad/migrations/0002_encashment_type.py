# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2020-11-09 18:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sklad', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='encashment',
            name='type',
            field=models.IntegerField(choices=[(1, '- \u0438\u0437\u044a\u044f\u0442\u0438\u0435'), (2, '- \u043e\u043f\u043b\u0430\u0442\u0430 \u043a\u0443\u0440\u044c\u0435\u0440\u0443'), (3, '- \u0441\u0434\u0430\u0447\u0430 \u043a\u0443\u0440\u044c\u0435\u0440\u0443'), (4, '- \u0432\u044a\u0435\u0437\u0434 \u043d\u0430 \u0442\u0435\u0440\u0440\u0438\u0442\u043e\u0440\u0438\u044e'), (5, '- \u043e\u043f\u043b\u0430\u0442\u0430 \u0434\u043e\u0441\u0442\u0430\u0432\u043e\u043a'), (80, '+ \u0412\u043d\u0435\u0441\u0435\u043d\u0438\u0435 \u0432 \u043a\u0430\u0441\u0441\u0443'), (90, '+- \u041f\u0440\u043e\u0447\u0435\u0435')], default=1, verbose_name='\u0422\u0438\u043f'),
        ),
    ]
