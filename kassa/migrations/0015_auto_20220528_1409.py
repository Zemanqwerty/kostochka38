# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2022-05-28 14:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kassa', '0014_encashment_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='encashment',
            name='type',
            field=models.IntegerField(choices=[(1, '- \u0418\u0437\u044a\u044f\u0442\u0438\u0435'), (2, '- \u0417\u041f'), (3, '- \u0412\u043e\u0437\u0432\u0440\u0430\u0442 \u043a\u043b\u0438\u0435\u043d\u0442\u0443'), (4, '+ \u0412\u043d\u0435\u0441\u0435\u043d\u0438\u0435 \u0441\u0434\u0430\u0447\u0438'), (9, '+- \u041f\u0440\u043e\u0447\u0435\u0435')], default=1, verbose_name='\u0422\u0438\u043f'),
        ),
    ]
