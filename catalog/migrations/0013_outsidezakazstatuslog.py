# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-15 19:18
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('catalog', '0012_auto_20160904_1804'),
    ]

    operations = [
        migrations.CreateModel(
            name='OutsideZakazStatusLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430')),
                ('status', models.IntegerField(choices=[(0, '\u041d\u043e\u0432\u044b\u0439'), (2, '\u0414\u043e\u0441\u0442\u0430\u0432\u043a\u0430 \u0441\u043e\u0433\u043b\u0430\u0441\u043e\u0432\u0430\u043d\u0430'), (4, '\u0417\u0430\u043a\u0430\u0437 \u043f\u043e\u043b\u0443\u0447\u0435\u043d'), (6, '\u0417\u0430\u0432\u0435\u0440\u0448\u0435\u043d')], default=0, verbose_name='\u0441\u0442\u0430\u0442\u0443\u0441 \u0437\u0430\u043a\u0430\u0437\u0430')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='\u041a\u0442\u043e \u0438\u0437\u043c\u0435\u043d\u0438\u043b')),
                ('zakaz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.OutsideZakaz', verbose_name='\u0417\u0430\u043a\u0430\u0437 \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0430')),
            ],
            options={
                'ordering': ['date'],
                'verbose_name': '\u041b\u043e\u0433 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f \u0441\u0442\u0430\u0442\u0443\u0441\u0430 \u0441\u0442\u043e\u0440\u043e\u043d\u043d\u0435\u0433\u043e \u0437\u0430\u043a\u0430\u0437\u0430',
                'verbose_name_plural': '\u041b\u043e\u0433 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f \u0441\u0442\u0430\u0442\u0443\u0441\u0430 \u0441\u0442\u043e\u0440\u043e\u043d\u043d\u0435\u0433\u043e \u0437\u0430\u043a\u0430\u0437\u0430',
            },
        ),
    ]
