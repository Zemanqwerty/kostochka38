# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2019-07-03 22:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0039_auto_20190314_2128'),
    ]

    operations = [
        migrations.AddField(
            model_name='tempzakazgoods',
            name='presale',
            field=models.BooleanField(default=False, verbose_name='\u041f\u0440\u0435\u0434\u0437\u0430\u043a\u0430\u0437'),
        ),
        migrations.AddField(
            model_name='zakazgoods',
            name='presale',
            field=models.BooleanField(default=False, verbose_name='\u041f\u0440\u0435\u0434\u0437\u0430\u043a\u0430\u0437'),
        ),
        migrations.AlterField(
            model_name='deckitem',
            name='availability',
            field=models.IntegerField(choices=[(0, '\u041d\u0435\u0442 \u0432 \u043d\u0430\u043b\u0438\u0447\u0438\u0438'), (3, '\u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438 \u0443 \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0430'), (10, '\u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438 \u043d\u0430 \u0441\u043a\u043b\u0430\u0434\u0435'), (20, '\u041f\u043e\u0434 \u0437\u0430\u043a\u0430\u0437')], default=3, verbose_name='\u041d\u0430\u043b\u0438\u0447\u0438\u0435 \u0442\u043e\u0432\u0430\u0440\u0430'),
        ),
        migrations.AlterField(
            model_name='deckitem',
            name='segment',
            field=models.CharField(choices=[(b'royal', '\u0420\u043e\u044f\u043b \u041a\u0430\u043d\u0438\u043d'), (b'purina', '\u041f\u0443\u0440\u0438\u043d\u0430'), (b'avrora', '\u0410\u0432\u0440\u043e\u0440\u0430'), (b'zooirkutsk', '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (b'slata', '\u0421\u043b\u0430\u0442\u0430'), (b'dogservice', '\u0414\u043e\u0433 \u0441\u0435\u0440\u0432\u0438\u0441'), (b'bosh', '\u0411\u043e\u0448'), (b'kronos', '\u041a\u0440\u043e\u043d\u043e\u0441'), (b'taobao', 'TaoBao'), (b'valta', '\u0412\u0430\u043b\u0442\u0430'), (b'karmi', '\u041a\u0430\u0440\u043c\u0438'), (b'velkorm', '\u0412\u0435\u043b\u043a\u043e\u0440\u043c'), (b'spectr', '\u0421\u043f\u0435\u043a\u0442\u0440'), (b'ivanko', '\u0418\u0432\u0430\u043d\u043a\u043e'), (b'pet-kontinent', '\u041f\u0435\u0442-\u041a\u043e\u043d\u0442\u0438\u043d\u0435\u043d\u0442'), (b'zebra', '\u0416\u0438\u0432\u043e\u0442\u043d\u044b\u0439 \u043c\u0438\u0440'), (b'uukolbasy', '\u0422\u0414 \u0423\u043b\u0430\u043d-\u0423\u0434\u044d\u043d\u0441\u043a\u0438\u0435 \u043a\u043e\u043b\u0431\u0430\u0441\u044b'), (b'nordeks', '\u041d\u043e\u0440\u0434\u044d\u043a\u0441')], max_length=32, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a'),
        ),
        migrations.AlterField(
            model_name='insidezakaz',
            name='supplier',
            field=models.IntegerField(choices=[(0, '\u041f\u0440\u043e\u043a\u0421\u0435\u0440\u0432\u0438\u0441 (\u041f\u0443\u0440\u0438\u043d\u0430)'), (1, '\u0420\u043e\u044f\u043b\u041a\u0430\u043d\u0438\u043d'), (2, '\u0410\u0432\u0440\u043e\u0440\u0430'), (3, '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (4, '\u0421\u043b\u0430\u0442\u0430'), (9, '\u0412\u0430\u043b\u0442\u0430'), (15, '\u041a\u0430\u0440\u043c\u0438'), (16, '\u0412\u0435\u043b\u043a\u043e\u0440\u043c'), (6, '\u0414\u043e\u0433\u0421\u0435\u0440\u0432\u0438\u0441'), (7, '\u041a\u0440\u043e\u043d\u043e\u0441'), (8, '\u0422\u0430\u043e\u0411\u0430\u043e'), (10, '\u0421\u043f\u0435\u043a\u0442\u0440'), (11, '\u0418\u0432\u0430\u043d\u043a\u043e'), (12, '\u041f\u0435\u0442-\u041a\u043e\u043d\u0442\u0438\u043d\u0435\u043d\u0442'), (13, '\u0416\u0438\u0432\u043e\u0442\u043d\u044b\u0439 \u043c\u0438\u0440'), (17, '\u0422\u0414 \u0423\u043b\u0430\u043d-\u0423\u0434\u044d\u043d\u0441\u043a\u0438\u0435 \u043a\u043e\u043b\u0431\u0430\u0441\u044b'), (14, '\u041d\u043e\u0440\u0434\u044d\u043a\u0441')], default=0, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a'),
        ),
        migrations.AlterField(
            model_name='item',
            name='availability',
            field=models.IntegerField(choices=[(0, '\u041d\u0435\u0442 \u0432 \u043d\u0430\u043b\u0438\u0447\u0438\u0438'), (3, '\u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438 \u0443 \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0430'), (10, '\u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438 \u043d\u0430 \u0441\u043a\u043b\u0430\u0434\u0435'), (20, '\u041f\u043e\u0434 \u0437\u0430\u043a\u0430\u0437')], default=3, verbose_name='\u041d\u0430\u043b\u0438\u0447\u0438\u0435 \u0442\u043e\u0432\u0430\u0440\u0430'),
        ),
        migrations.AlterField(
            model_name='itemavailabilitylog',
            name='availability',
            field=models.IntegerField(choices=[(0, '\u041d\u0435\u0442 \u0432 \u043d\u0430\u043b\u0438\u0447\u0438\u0438'), (3, '\u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438 \u0443 \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0430'), (10, '\u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438 \u043d\u0430 \u0441\u043a\u043b\u0430\u0434\u0435'), (20, '\u041f\u043e\u0434 \u0437\u0430\u043a\u0430\u0437')], verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441 \u043d\u0430\u043b\u0438\u0447\u0438\u044f'),
        ),
        migrations.AlterField(
            model_name='parserlog',
            name='segment',
            field=models.CharField(blank=True, choices=[(b'royal', '\u0420\u043e\u044f\u043b \u041a\u0430\u043d\u0438\u043d'), (b'purina', '\u041f\u0443\u0440\u0438\u043d\u0430'), (b'avrora', '\u0410\u0432\u0440\u043e\u0440\u0430'), (b'zooirkutsk', '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (b'slata', '\u0421\u043b\u0430\u0442\u0430'), (b'dogservice', '\u0414\u043e\u0433 \u0441\u0435\u0440\u0432\u0438\u0441'), (b'bosh', '\u0411\u043e\u0448'), (b'kronos', '\u041a\u0440\u043e\u043d\u043e\u0441'), (b'taobao', 'TaoBao'), (b'valta', '\u0412\u0430\u043b\u0442\u0430'), (b'karmi', '\u041a\u0430\u0440\u043c\u0438'), (b'velkorm', '\u0412\u0435\u043b\u043a\u043e\u0440\u043c'), (b'spectr', '\u0421\u043f\u0435\u043a\u0442\u0440'), (b'ivanko', '\u0418\u0432\u0430\u043d\u043a\u043e'), (b'pet-kontinent', '\u041f\u0435\u0442-\u041a\u043e\u043d\u0442\u0438\u043d\u0435\u043d\u0442'), (b'zebra', '\u0416\u0438\u0432\u043e\u0442\u043d\u044b\u0439 \u043c\u0438\u0440'), (b'uukolbasy', '\u0422\u0414 \u0423\u043b\u0430\u043d-\u0423\u0434\u044d\u043d\u0441\u043a\u0438\u0435 \u043a\u043e\u043b\u0431\u0430\u0441\u044b'), (b'nordeks', '\u041d\u043e\u0440\u0434\u044d\u043a\u0441')], max_length=32, null=True, verbose_name='\u0421\u0435\u0433\u043c\u0435\u043d\u0442'),
        ),
        migrations.AlterField(
            model_name='priceparser',
            name='supplier',
            field=models.IntegerField(choices=[(0, '\u041f\u0440\u043e\u043a\u0421\u0435\u0440\u0432\u0438\u0441 (\u041f\u0443\u0440\u0438\u043d\u0430)'), (1, '\u0420\u043e\u044f\u043b\u041a\u0430\u043d\u0438\u043d'), (2, '\u0410\u0432\u0440\u043e\u0440\u0430'), (3, '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (4, '\u0421\u043b\u0430\u0442\u0430'), (9, '\u0412\u0430\u043b\u0442\u0430'), (15, '\u041a\u0430\u0440\u043c\u0438'), (16, '\u0412\u0435\u043b\u043a\u043e\u0440\u043c'), (6, '\u0414\u043e\u0433\u0421\u0435\u0440\u0432\u0438\u0441'), (7, '\u041a\u0440\u043e\u043d\u043e\u0441'), (8, '\u0422\u0430\u043e\u0411\u0430\u043e'), (10, '\u0421\u043f\u0435\u043a\u0442\u0440'), (11, '\u0418\u0432\u0430\u043d\u043a\u043e'), (12, '\u041f\u0435\u0442-\u041a\u043e\u043d\u0442\u0438\u043d\u0435\u043d\u0442'), (13, '\u0416\u0438\u0432\u043e\u0442\u043d\u044b\u0439 \u043c\u0438\u0440'), (17, '\u0422\u0414 \u0423\u043b\u0430\u043d-\u0423\u0434\u044d\u043d\u0441\u043a\u0438\u0435 \u043a\u043e\u043b\u0431\u0430\u0441\u044b'), (14, '\u041d\u043e\u0440\u0434\u044d\u043a\u0441')], default=1, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a'),
        ),
        migrations.AlterField(
            model_name='producer',
            name='segment',
            field=models.CharField(blank=True, choices=[(b'royal', '\u0420\u043e\u044f\u043b \u041a\u0430\u043d\u0438\u043d'), (b'purina', '\u041f\u0443\u0440\u0438\u043d\u0430'), (b'avrora', '\u0410\u0432\u0440\u043e\u0440\u0430'), (b'zooirkutsk', '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (b'slata', '\u0421\u043b\u0430\u0442\u0430'), (b'dogservice', '\u0414\u043e\u0433 \u0441\u0435\u0440\u0432\u0438\u0441'), (b'bosh', '\u0411\u043e\u0448'), (b'kronos', '\u041a\u0440\u043e\u043d\u043e\u0441'), (b'taobao', 'TaoBao'), (b'valta', '\u0412\u0430\u043b\u0442\u0430'), (b'karmi', '\u041a\u0430\u0440\u043c\u0438'), (b'velkorm', '\u0412\u0435\u043b\u043a\u043e\u0440\u043c'), (b'spectr', '\u0421\u043f\u0435\u043a\u0442\u0440'), (b'ivanko', '\u0418\u0432\u0430\u043d\u043a\u043e'), (b'pet-kontinent', '\u041f\u0435\u0442-\u041a\u043e\u043d\u0442\u0438\u043d\u0435\u043d\u0442'), (b'zebra', '\u0416\u0438\u0432\u043e\u0442\u043d\u044b\u0439 \u043c\u0438\u0440'), (b'uukolbasy', '\u0422\u0414 \u0423\u043b\u0430\u043d-\u0423\u0434\u044d\u043d\u0441\u043a\u0438\u0435 \u043a\u043e\u043b\u0431\u0430\u0441\u044b'), (b'nordeks', '\u041d\u043e\u0440\u0434\u044d\u043a\u0441')], max_length=32, null=True, verbose_name='\u0421\u0435\u0433\u043c\u0435\u043d\u0442'),
        ),
        migrations.AlterField(
            model_name='saletable',
            name='supplier',
            field=models.IntegerField(choices=[(0, '\u041f\u0440\u043e\u043a\u0421\u0435\u0440\u0432\u0438\u0441 (\u041f\u0443\u0440\u0438\u043d\u0430)'), (1, '\u0420\u043e\u044f\u043b\u041a\u0430\u043d\u0438\u043d'), (2, '\u0410\u0432\u0440\u043e\u0440\u0430'), (3, '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (4, '\u0421\u043b\u0430\u0442\u0430'), (9, '\u0412\u0430\u043b\u0442\u0430'), (15, '\u041a\u0430\u0440\u043c\u0438'), (16, '\u0412\u0435\u043b\u043a\u043e\u0440\u043c'), (6, '\u0414\u043e\u0433\u0421\u0435\u0440\u0432\u0438\u0441'), (7, '\u041a\u0440\u043e\u043d\u043e\u0441'), (8, '\u0422\u0430\u043e\u0411\u0430\u043e'), (10, '\u0421\u043f\u0435\u043a\u0442\u0440'), (11, '\u0418\u0432\u0430\u043d\u043a\u043e'), (12, '\u041f\u0435\u0442-\u041a\u043e\u043d\u0442\u0438\u043d\u0435\u043d\u0442'), (13, '\u0416\u0438\u0432\u043e\u0442\u043d\u044b\u0439 \u043c\u0438\u0440'), (17, '\u0422\u0414 \u0423\u043b\u0430\u043d-\u0423\u0434\u044d\u043d\u0441\u043a\u0438\u0435 \u043a\u043e\u043b\u0431\u0430\u0441\u044b'), (14, '\u041d\u043e\u0440\u0434\u044d\u043a\u0441')], default=0, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a'),
        ),
        migrations.AlterField(
            model_name='vendoraccount',
            name='supplier',
            field=models.IntegerField(choices=[(0, '\u041f\u0440\u043e\u043a\u0421\u0435\u0440\u0432\u0438\u0441 (\u041f\u0443\u0440\u0438\u043d\u0430)'), (1, '\u0420\u043e\u044f\u043b\u041a\u0430\u043d\u0438\u043d'), (2, '\u0410\u0432\u0440\u043e\u0440\u0430'), (3, '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (4, '\u0421\u043b\u0430\u0442\u0430'), (9, '\u0412\u0430\u043b\u0442\u0430'), (15, '\u041a\u0430\u0440\u043c\u0438'), (16, '\u0412\u0435\u043b\u043a\u043e\u0440\u043c'), (6, '\u0414\u043e\u0433\u0421\u0435\u0440\u0432\u0438\u0441'), (7, '\u041a\u0440\u043e\u043d\u043e\u0441'), (8, '\u0422\u0430\u043e\u0411\u0430\u043e'), (10, '\u0421\u043f\u0435\u043a\u0442\u0440'), (11, '\u0418\u0432\u0430\u043d\u043a\u043e'), (12, '\u041f\u0435\u0442-\u041a\u043e\u043d\u0442\u0438\u043d\u0435\u043d\u0442'), (13, '\u0416\u0438\u0432\u043e\u0442\u043d\u044b\u0439 \u043c\u0438\u0440'), (17, '\u0422\u0414 \u0423\u043b\u0430\u043d-\u0423\u0434\u044d\u043d\u0441\u043a\u0438\u0435 \u043a\u043e\u043b\u0431\u0430\u0441\u044b'), (14, '\u041d\u043e\u0440\u0434\u044d\u043a\u0441')], default=1, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a'),
        ),
    ]