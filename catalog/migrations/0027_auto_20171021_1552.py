# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-10-21 15:52
from __future__ import unicode_literals

import catalog.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0026_zakaz_real_sum'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriceParser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438')),
                ('supplier', models.IntegerField(choices=[(0, '\u041f\u0440\u043e\u043a\u0421\u0435\u0440\u0432\u0438\u0441 (\u041f\u0443\u0440\u0438\u043d\u0430)'), (1, '\u0420\u043e\u044f\u043b\u041a\u0430\u043d\u0438\u043d'), (2, '\u0410\u0432\u0440\u043e\u0440\u0430'), (3, '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (4, '\u0421\u043b\u0430\u0442\u0430'), (9, '\u0412\u0430\u043b\u0442\u0430'), (6, '\u0414\u043e\u0433\u0421\u0435\u0440\u0432\u0438\u0441'), (7, '\u041a\u0440\u043e\u043d\u043e\u0441'), (8, '\u0422\u0430\u043e\u0411\u0430\u043e'), (10, '\u0421\u043f\u0435\u043a\u0442\u0440'), (11, '\u0418\u0432\u0430\u043d\u043a\u043e'), (12, '\u041f\u0435\u0442-\u041a\u043e\u043d\u0442\u0438\u043d\u0435\u043d\u0442')], default=1, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a')),
                ('status', models.IntegerField(choices=[(1, '\u041d\u043e\u0432\u044b\u0439'), (2, '\u0412\u044b\u043f\u043e\u043b\u043d\u0435\u043d'), (3, '\u0412 \u043f\u0440\u043e\u0446\u0435\u0441\u0441\u0435'), (4, '\u041e\u0448\u0438\u0431\u043a\u0430')], default=1, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441')),
                ('price_file', models.FileField(upload_to=catalog.models.get_file_path, verbose_name='\u041f\u0440\u0430\u0439\u0441')),
                ('extra', models.TextField(verbose_name='\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439')),
            ],
            options={
                'verbose_name': '\u041f\u0440\u0430\u0439\u0441 \u0434\u043b\u044f \u043f\u0430\u0440\u0441\u0438\u043d\u0433\u0430',
                'verbose_name_plural': '\u043f\u0440\u0430\u0439\u0441\u044b \u0434\u043b\u044f \u043f\u0430\u0440\u0441\u0438\u043d\u0433\u0430',
            },
        ),
        migrations.AlterField(
            model_name='zakaz',
            name='manager',
            field=models.ForeignKey(blank=True, default=486, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='manager_zakaz_set', to=settings.AUTH_USER_MODEL, verbose_name='\u041c\u0435\u043d\u0435\u0434\u0436\u0435\u0440'),
        ),
    ]
