# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2021-05-30 20:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0010_auto_20200610_1527'),
        ('catalog', '0091_insidezakaz_details'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemPriceChange',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_processed', models.BooleanField(default=False, verbose_name='\u041e\u0431\u0440\u0430\u0431\u043e\u0442\u0430\u043d\u043e')),
                ('date', models.DateField(auto_now_add=True, help_text='\u0421\u043e\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0443\u0435\u0442 \u0434\u0430\u0442\u0435, \u043a\u043e\u0433\u0434\u0430 \u0431\u044b\u043b \u0437\u0430\u043f\u0443\u0449\u0435\u043d \u043f\u0430\u0440\u0441\u0435\u0440 \u0446\u0435\u043d, \u0441\u043e\u0437\u0434\u0430\u0432\u0448\u0438\u0439 \u0434\u0430\u043d\u043d\u0443\u044e \u0437\u0430\u043f\u0438\u0441\u044c \u0432 \u0431\u0430\u0437\u0435', verbose_name='\u0414\u0430\u0442\u0430 \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.Item', verbose_name='\u0422\u043e\u0432\u0430\u0440 (\u0432\u0435\u0441/\u0442\u0438\u043f \u0441 \u0446\u0435\u043d\u043e\u0439)')),
                ('warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.WareHouse', verbose_name='\u041c\u0430\u0433\u0430\u0437\u0438\u043d')),
            ],
            options={
                'ordering': ['-date'],
                'verbose_name': '\u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0435 \u043f\u0440\u0430\u0439\u0441\u0430',
                'verbose_name_plural': '\u0418\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f \u043f\u0440\u0430\u0439\u0441\u043e\u0432',
            },
        ),
        migrations.AlterModelOptions(
            name='itemphoto',
            options={'ordering': ['order'], 'verbose_name': '\u0424\u043e\u0442\u043e \u0442\u043e\u0432\u0430\u0440\u0430', 'verbose_name_plural': '\u0424\u043e\u0442\u043e \u0442\u043e\u0432\u0430\u0440\u0430'},
        ),
        migrations.AddField(
            model_name='insidezakazgoods',
            name='action',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='news.New', verbose_name=b'\xd0\x90\xd0\xba\xd1\x86\xd0\xb8\xd1\x8f'),
        ),
        migrations.AddField(
            model_name='itemphoto',
            name='order',
            field=models.PositiveSmallIntegerField(default=99, verbose_name='\u041f\u043e\u0440\u044f\u0434\u043e\u043a'),
        ),
        migrations.AddField(
            model_name='tempzakaz',
            name='availability_changed',
            field=models.BooleanField(default=False, help_text='\u0423\u0441\u0442\u043e\u043d\u0430\u0432\u043b\u0438\u0432\u0430\u0435\u0442\u0441\u044f \u0432 "True", \u0435\u0441\u043b\u0438 \u043d\u0430\u043b\u0438\u0447\u0438\u0435 \u0445\u043e\u0442\u044f \u0431\u044b \u043e\u0434\u043d\u043e\u0433\u043e \u0442\u043e\u0432\u0430\u0440\u0430 \u0438\u0437 \u043a\u043e\u0440\u0437\u0438\u043d\u044b \u0431\u044b\u043b\u043e \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u043e. \u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0435\u0442\u0441\u044f \u0434\u043b\u044f \u0442\u043e\u0433\u043e, \u0447\u0442\u043e\u0431\u044b \u041e\u0414\u0418\u041d \u0440\u0430\u0437 \u0443\u0432\u0435\u0434\u043e\u043c\u0438\u0442\u044c \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f \u043e\u0431 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0438 \u043d\u0430\u043b\u0438\u0447\u0438\u044f \u0442\u043e\u0432\u0430\u0440\u0430 \u0432 \u0437\u0430\u043a\u0430\u0437\u0435', verbose_name='\u041d\u0430\u043b\u0438\u0447\u0438\u0435 \u0442\u043e\u0432\u0430\u0440\u0430 \u0432 \u043a\u043e\u0440\u0437\u0438\u043d\u0435 \u0438\u0437\u043c\u0435\u043d\u0438\u043b\u043e\u0441\u044c'),
        ),
        migrations.AddField(
            model_name='tempzakaz',
            name='summ_changed',
            field=models.BooleanField(default=False, help_text='\u0423\u0441\u0442\u043e\u043d\u0430\u0432\u043b\u0438\u0432\u0430\u0435\u0442\u0441\u044f \u0432 "True", \u0435\u0441\u043b\u0438 \u0441\u0442\u043e\u0438\u043c\u043e\u0441\u0442\u044c \u0445\u043e\u0442\u044f \u0431\u044b \u043e\u0434\u043d\u043e\u0433\u043e \u0442\u043e\u0432\u0430\u0440\u0430 \u0438\u0437 \u043a\u043e\u0440\u0437\u0438\u043d\u044b \u0431\u044b\u043b\u0430 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0430. \u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0435\u0442\u0441\u044f \u0434\u043b\u044f \u0442\u043e\u0433\u043e, \u0447\u0442\u043e\u0431\u044b \u041e\u0414\u0418\u041d \u0440\u0430\u0437 \u0443\u0432\u0435\u0434\u043e\u043c\u0438\u0442\u044c \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f \u043e\u0431 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0438 \u0441\u0443\u043c\u043c\u044b \u0437\u0430\u043a\u0430\u0437\u0430', verbose_name='\u0421\u0443\u043c\u043c\u0430 \u043a\u043e\u0440\u0437\u0438\u043d\u044b \u0438\u0437\u043c\u0435\u043d\u0438\u043b\u0430\u0441\u044c'),
        ),
        migrations.AddField(
            model_name='tempzakazgoods',
            name='action',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='news.New', verbose_name=b'\xd0\x90\xd0\xba\xd1\x86\xd0\xb8\xd1\x8f'),
        ),
        migrations.AddField(
            model_name='zakazgoods',
            name='action',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='news.New', verbose_name=b'\xd0\x90\xd0\xba\xd1\x86\xd0\xb8\xd1\x8f'),
        ),
        migrations.AlterField(
            model_name='insidezakaz',
            name='sale_koef',
            field=models.FloatField(default=0, verbose_name='\u0421\u043a\u0438\u0434\u043a\u0430 %'),
        ),
        migrations.AlterField(
            model_name='insidezakazgoods',
            name='sale',
            field=models.FloatField(blank=True, null=True, verbose_name='\u0441\u043a\u0438\u0434\u043a\u0430 %'),
        ),
        migrations.AlterField(
            model_name='saletable',
            name='value',
            field=models.FloatField(default=0, verbose_name='\u0420\u0430\u0437\u043c\u0435\u0440 \u0441\u043a\u0438\u0434\u043a\u0438'),
        ),
        migrations.AlterField(
            model_name='zakaz',
            name='dostavka',
            field=models.IntegerField(default=0, verbose_name='\u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0430/-\u0441\u043a\u0438\u0434\u043a\u0430'),
        ),
    ]
