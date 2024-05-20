# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-11-19 13:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0027_auto_20171021_1552'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deckitem',
            name='segment',
            field=models.CharField(choices=[(b'royal', '\u0420\u043e\u044f\u043b \u041a\u0430\u043d\u0438\u043d'), (b'purina', '\u041f\u0443\u0440\u0438\u043d\u0430'), (b'avrora', '\u0410\u0432\u0440\u043e\u0440\u0430'), (b'zooirkutsk', '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (b'slata', '\u0421\u043b\u0430\u0442\u0430'), (b'dogservice', '\u0414\u043e\u0433 \u0441\u0435\u0440\u0432\u0438\u0441'), (b'bosh', '\u0411\u043e\u0448'), (b'kronos', '\u041a\u0440\u043e\u043d\u043e\u0441'), (b'taobao', 'TaoBao'), (b'valta', '\u0412\u0430\u043b\u0442\u0430'), (b'spectr', '\u0421\u043f\u0435\u043a\u0442\u0440'), (b'ivanko', '\u0418\u0432\u0430\u043d\u043a\u043e'), (b'pet-kontinent', '\u041f\u0435\u0442-\u041a\u043e\u043d\u0442\u0438\u043d\u0435\u043d\u0442'), (b'zebra', '\u0416\u0438\u0432\u043e\u0442\u043d\u044b\u0439 \u043c\u0438\u0440'), (b'nordeks', '\u041d\u043e\u0440\u0434\u044d\u043a\u0441')], max_length=32, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a'),
        ),
        migrations.AlterField(
            model_name='insidezakaz',
            name='supplier',
            field=models.IntegerField(choices=[(0, '\u041f\u0440\u043e\u043a\u0421\u0435\u0440\u0432\u0438\u0441 (\u041f\u0443\u0440\u0438\u043d\u0430)'), (1, '\u0420\u043e\u044f\u043b\u041a\u0430\u043d\u0438\u043d'), (2, '\u0410\u0432\u0440\u043e\u0440\u0430'), (3, '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (4, '\u0421\u043b\u0430\u0442\u0430'), (9, '\u0412\u0430\u043b\u0442\u0430'), (6, '\u0414\u043e\u0433\u0421\u0435\u0440\u0432\u0438\u0441'), (7, '\u041a\u0440\u043e\u043d\u043e\u0441'), (8, '\u0422\u0430\u043e\u0411\u0430\u043e'), (10, '\u0421\u043f\u0435\u043a\u0442\u0440'), (11, '\u0418\u0432\u0430\u043d\u043a\u043e'), (12, '\u041f\u0435\u0442-\u041a\u043e\u043d\u0442\u0438\u043d\u0435\u043d\u0442'), (13, '\u0416\u0438\u0432\u043e\u0442\u043d\u044b\u0439 \u043c\u0438\u0440'), (14, '\u041d\u043e\u0440\u0434\u044d\u043a\u0441')], default=0, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a'),
        ),
        migrations.AlterField(
            model_name='parserlog',
            name='segment',
            field=models.CharField(blank=True, choices=[(b'royal', '\u0420\u043e\u044f\u043b \u041a\u0430\u043d\u0438\u043d'), (b'purina', '\u041f\u0443\u0440\u0438\u043d\u0430'), (b'avrora', '\u0410\u0432\u0440\u043e\u0440\u0430'), (b'zooirkutsk', '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (b'slata', '\u0421\u043b\u0430\u0442\u0430'), (b'dogservice', '\u0414\u043e\u0433 \u0441\u0435\u0440\u0432\u0438\u0441'), (b'bosh', '\u0411\u043e\u0448'), (b'kronos', '\u041a\u0440\u043e\u043d\u043e\u0441'), (b'taobao', 'TaoBao'), (b'valta', '\u0412\u0430\u043b\u0442\u0430'), (b'spectr', '\u0421\u043f\u0435\u043a\u0442\u0440'), (b'ivanko', '\u0418\u0432\u0430\u043d\u043a\u043e'), (b'pet-kontinent', '\u041f\u0435\u0442-\u041a\u043e\u043d\u0442\u0438\u043d\u0435\u043d\u0442'), (b'zebra', '\u0416\u0438\u0432\u043e\u0442\u043d\u044b\u0439 \u043c\u0438\u0440'), (b'nordeks', '\u041d\u043e\u0440\u0434\u044d\u043a\u0441')], max_length=32, null=True, verbose_name='\u0421\u0435\u0433\u043c\u0435\u043d\u0442'),
        ),
        migrations.AlterField(
            model_name='priceparser',
            name='extra',
            field=models.TextField(blank=True, null=True, verbose_name='\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439'),
        ),
        migrations.AlterField(
            model_name='priceparser',
            name='supplier',
            field=models.IntegerField(choices=[(0, '\u041f\u0440\u043e\u043a\u0421\u0435\u0440\u0432\u0438\u0441 (\u041f\u0443\u0440\u0438\u043d\u0430)'), (1, '\u0420\u043e\u044f\u043b\u041a\u0430\u043d\u0438\u043d'), (2, '\u0410\u0432\u0440\u043e\u0440\u0430'), (3, '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (4, '\u0421\u043b\u0430\u0442\u0430'), (9, '\u0412\u0430\u043b\u0442\u0430'), (6, '\u0414\u043e\u0433\u0421\u0435\u0440\u0432\u0438\u0441'), (7, '\u041a\u0440\u043e\u043d\u043e\u0441'), (8, '\u0422\u0430\u043e\u0411\u0430\u043e'), (10, '\u0421\u043f\u0435\u043a\u0442\u0440'), (11, '\u0418\u0432\u0430\u043d\u043a\u043e'), (12, '\u041f\u0435\u0442-\u041a\u043e\u043d\u0442\u0438\u043d\u0435\u043d\u0442'), (13, '\u0416\u0438\u0432\u043e\u0442\u043d\u044b\u0439 \u043c\u0438\u0440'), (14, '\u041d\u043e\u0440\u0434\u044d\u043a\u0441')], default=1, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a'),
        ),
        migrations.AlterField(
            model_name='producer',
            name='segment',
            field=models.CharField(blank=True, choices=[(b'royal', '\u0420\u043e\u044f\u043b \u041a\u0430\u043d\u0438\u043d'), (b'purina', '\u041f\u0443\u0440\u0438\u043d\u0430'), (b'avrora', '\u0410\u0432\u0440\u043e\u0440\u0430'), (b'zooirkutsk', '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (b'slata', '\u0421\u043b\u0430\u0442\u0430'), (b'dogservice', '\u0414\u043e\u0433 \u0441\u0435\u0440\u0432\u0438\u0441'), (b'bosh', '\u0411\u043e\u0448'), (b'kronos', '\u041a\u0440\u043e\u043d\u043e\u0441'), (b'taobao', 'TaoBao'), (b'valta', '\u0412\u0430\u043b\u0442\u0430'), (b'spectr', '\u0421\u043f\u0435\u043a\u0442\u0440'), (b'ivanko', '\u0418\u0432\u0430\u043d\u043a\u043e'), (b'pet-kontinent', '\u041f\u0435\u0442-\u041a\u043e\u043d\u0442\u0438\u043d\u0435\u043d\u0442'), (b'zebra', '\u0416\u0438\u0432\u043e\u0442\u043d\u044b\u0439 \u043c\u0438\u0440'), (b'nordeks', '\u041d\u043e\u0440\u0434\u044d\u043a\u0441')], max_length=32, null=True, verbose_name='\u0421\u0435\u0433\u043c\u0435\u043d\u0442'),
        ),
        migrations.AlterField(
            model_name='saletable',
            name='supplier',
            field=models.IntegerField(choices=[(0, '\u041f\u0440\u043e\u043a\u0421\u0435\u0440\u0432\u0438\u0441 (\u041f\u0443\u0440\u0438\u043d\u0430)'), (1, '\u0420\u043e\u044f\u043b\u041a\u0430\u043d\u0438\u043d'), (2, '\u0410\u0432\u0440\u043e\u0440\u0430'), (3, '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (4, '\u0421\u043b\u0430\u0442\u0430'), (9, '\u0412\u0430\u043b\u0442\u0430'), (6, '\u0414\u043e\u0433\u0421\u0435\u0440\u0432\u0438\u0441'), (7, '\u041a\u0440\u043e\u043d\u043e\u0441'), (8, '\u0422\u0430\u043e\u0411\u0430\u043e'), (10, '\u0421\u043f\u0435\u043a\u0442\u0440'), (11, '\u0418\u0432\u0430\u043d\u043a\u043e'), (12, '\u041f\u0435\u0442-\u041a\u043e\u043d\u0442\u0438\u043d\u0435\u043d\u0442'), (13, '\u0416\u0438\u0432\u043e\u0442\u043d\u044b\u0439 \u043c\u0438\u0440'), (14, '\u041d\u043e\u0440\u0434\u044d\u043a\u0441')], default=0, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a'),
        ),
        migrations.AlterField(
            model_name='vendoraccount',
            name='supplier',
            field=models.IntegerField(choices=[(0, '\u041f\u0440\u043e\u043a\u0421\u0435\u0440\u0432\u0438\u0441 (\u041f\u0443\u0440\u0438\u043d\u0430)'), (1, '\u0420\u043e\u044f\u043b\u041a\u0430\u043d\u0438\u043d'), (2, '\u0410\u0432\u0440\u043e\u0440\u0430'), (3, '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (4, '\u0421\u043b\u0430\u0442\u0430'), (9, '\u0412\u0430\u043b\u0442\u0430'), (6, '\u0414\u043e\u0433\u0421\u0435\u0440\u0432\u0438\u0441'), (7, '\u041a\u0440\u043e\u043d\u043e\u0441'), (8, '\u0422\u0430\u043e\u0411\u0430\u043e'), (10, '\u0421\u043f\u0435\u043a\u0442\u0440'), (11, '\u0418\u0432\u0430\u043d\u043a\u043e'), (12, '\u041f\u0435\u0442-\u041a\u043e\u043d\u0442\u0438\u043d\u0435\u043d\u0442'), (13, '\u0416\u0438\u0432\u043e\u0442\u043d\u044b\u0439 \u043c\u0438\u0440'), (14, '\u041d\u043e\u0440\u0434\u044d\u043a\u0441')], default=1, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a'),
        ),
    ]