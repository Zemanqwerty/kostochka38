# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-07-11 21:17
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('catalog', '0005_auto_20160615_1632'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutoZakaz',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430 \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f')),
                ('repeat_period', models.PositiveIntegerField(default=30, help_text='\u0432 \u0434\u043d\u044f\u0445', verbose_name='\u041f\u0435\u0440\u0438\u043e\u0434 \u043f\u043e\u0432\u0442\u043e\u0440\u0430')),
                ('last_order', models.DateTimeField(verbose_name='\u0414\u0430\u0442\u0430 \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0435\u0433\u043e \u0430\u0432\u0442\u043e\u043f\u043e\u0432\u0442\u043e\u0440\u0430')),
                ('extra', models.TextField(blank=True, null=True, verbose_name='\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439 \u043c\u0435\u043d\u0435\u0434\u0436\u0435\u0440\u0430 \u043c\u0430\u0433\u0430\u0437\u0438\u043d\u0430')),
                ('repear_count', models.PositiveIntegerField(default=0, verbose_name='\u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e \u043f\u043e\u0432\u0442\u043e\u0440\u043e\u0432')),
                ('active', models.BooleanField(default=True, verbose_name='\u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0439')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c')),
                ('zakaz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.Zakaz', verbose_name='\u0420\u043e\u0434\u0438\u0442\u0435\u043b\u044c\u0441\u043a\u0438\u0439 \u0437\u0430\u043a\u0430\u0437')),
            ],
            options={
                'verbose_name': '\u0410\u0432\u0442\u043e\u0437\u0430\u043a\u0430\u0437',
                'verbose_name_plural': '\u0410\u0432\u0442\u043e\u0437\u0430\u043a\u0430\u0437\u044b',
            },
        ),
        migrations.CreateModel(
            name='AutoZakazGoods',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.Item')),
                ('zakaz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.AutoZakaz')),
            ],
            options={
                'ordering': ['item__deckitem__producer', 'id'],
                'verbose_name': '\u0422\u043e\u0432\u0430\u0440 \u0432 \u0430\u0432\u0442\u043e\u0437\u0430\u043a\u0430\u0437\u0435',
                'verbose_name_plural': '\u0422\u043e\u0432\u0430\u0440\u044b \u0432 \u0430\u0432\u0442\u043e\u0437\u0430\u043a\u0430\u0437\u0435',
            },
        ),
        migrations.CreateModel(
            name='AutoZakazStatusLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430')),
                ('autozakaz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.AutoZakaz', verbose_name='\u0410\u0432\u0442\u043e\u0437\u0430\u043a\u0430\u0437')),
                ('zakaz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.Zakaz', verbose_name='\u0417\u0430\u043a\u0430\u0437')),
            ],
            options={
                'ordering': ['date'],
                'verbose_name': '\u041b\u043e\u0433 \u0433\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u0438 \u0430\u0432\u0442\u043e\u0437\u0430\u043a\u0430\u0437\u043e\u0432',
                'verbose_name_plural': '\u041b\u043e\u0433 \u0433\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u0438 \u0430\u0432\u0442\u043e\u0437\u0430\u043a\u0430\u0437\u043e\u0432',
            },
        ),
        migrations.DeleteModel(
            name='AutoZakad',
        ),
        migrations.AlterField(
            model_name='deckitem',
            name='segment',
            field=models.CharField(choices=[(b'royal', '\u0420\u043e\u044f\u043b \u041a\u0430\u043d\u0438\u043d'), (b'purina', '\u041f\u0443\u0440\u0438\u043d\u0430'), (b'avrora', '\u0410\u0432\u0440\u043e\u0440\u0430'), (b'zooirkutsk', '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (b'slata', '\u0421\u043b\u0430\u0442\u0430'), (b'dogservice', '\u0414\u043e\u0433 \u0441\u0435\u0440\u0432\u0438\u0441'), (b'bosh', '\u0411\u043e\u0448'), (b'kronos', '\u041a\u0440\u043e\u043d\u043e\u0441'), (b'taobao', 'TaoBao'), (b'valta', '\u0412\u0430\u043b\u0442\u0430')], max_length=32, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a'),
        ),
        migrations.AlterField(
            model_name='insidezakaz',
            name='supplier',
            field=models.IntegerField(choices=[(0, '\u041f\u0440\u043e\u043a\u0421\u0435\u0440\u0432\u0438\u0441 (\u041f\u0443\u0440\u0438\u043d\u0430)'), (1, '\u0420\u043e\u044f\u043b\u041a\u0430\u043d\u0438\u043d'), (2, '\u0410\u0432\u0440\u043e\u0440\u0430'), (3, '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (4, '\u0421\u043b\u0430\u0442\u0430'), (9, '\u0412\u0430\u043b\u0442\u0430'), (6, '\u0414\u043e\u0433\u0421\u0435\u0440\u0432\u0438\u0441'), (7, '\u041a\u0440\u043e\u043d\u043e\u0441'), (8, '\u0422\u0430\u043e\u0411\u0430\u043e')], default=0, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a'),
        ),
        migrations.AlterField(
            model_name='parserlog',
            name='segment',
            field=models.CharField(blank=True, choices=[(b'royal', '\u0420\u043e\u044f\u043b \u041a\u0430\u043d\u0438\u043d'), (b'purina', '\u041f\u0443\u0440\u0438\u043d\u0430'), (b'avrora', '\u0410\u0432\u0440\u043e\u0440\u0430'), (b'zooirkutsk', '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (b'slata', '\u0421\u043b\u0430\u0442\u0430'), (b'dogservice', '\u0414\u043e\u0433 \u0441\u0435\u0440\u0432\u0438\u0441'), (b'bosh', '\u0411\u043e\u0448'), (b'kronos', '\u041a\u0440\u043e\u043d\u043e\u0441'), (b'taobao', 'TaoBao'), (b'valta', '\u0412\u0430\u043b\u0442\u0430')], max_length=32, null=True, verbose_name='\u0421\u0435\u0433\u043c\u0435\u043d\u0442'),
        ),
        migrations.AlterField(
            model_name='producer',
            name='segment',
            field=models.CharField(blank=True, choices=[(b'royal', '\u0420\u043e\u044f\u043b \u041a\u0430\u043d\u0438\u043d'), (b'purina', '\u041f\u0443\u0440\u0438\u043d\u0430'), (b'avrora', '\u0410\u0432\u0440\u043e\u0440\u0430'), (b'zooirkutsk', '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (b'slata', '\u0421\u043b\u0430\u0442\u0430'), (b'dogservice', '\u0414\u043e\u0433 \u0441\u0435\u0440\u0432\u0438\u0441'), (b'bosh', '\u0411\u043e\u0448'), (b'kronos', '\u041a\u0440\u043e\u043d\u043e\u0441'), (b'taobao', 'TaoBao'), (b'valta', '\u0412\u0430\u043b\u0442\u0430')], max_length=32, null=True, verbose_name='\u0421\u0435\u0433\u043c\u0435\u043d\u0442'),
        ),
        migrations.AlterField(
            model_name='saletable',
            name='supplier',
            field=models.IntegerField(choices=[(0, '\u041f\u0440\u043e\u043a\u0421\u0435\u0440\u0432\u0438\u0441 (\u041f\u0443\u0440\u0438\u043d\u0430)'), (1, '\u0420\u043e\u044f\u043b\u041a\u0430\u043d\u0438\u043d'), (2, '\u0410\u0432\u0440\u043e\u0440\u0430'), (3, '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (4, '\u0421\u043b\u0430\u0442\u0430'), (9, '\u0412\u0430\u043b\u0442\u0430'), (6, '\u0414\u043e\u0433\u0421\u0435\u0440\u0432\u0438\u0441'), (7, '\u041a\u0440\u043e\u043d\u043e\u0441'), (8, '\u0422\u0430\u043e\u0411\u0430\u043e')], default=0, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a'),
        ),
        migrations.AlterField(
            model_name='vendoraccount',
            name='supplier',
            field=models.IntegerField(choices=[(0, '\u041f\u0440\u043e\u043a\u0421\u0435\u0440\u0432\u0438\u0441 (\u041f\u0443\u0440\u0438\u043d\u0430)'), (1, '\u0420\u043e\u044f\u043b\u041a\u0430\u043d\u0438\u043d'), (2, '\u0410\u0432\u0440\u043e\u0440\u0430'), (3, '\u0417\u043e\u043e\u0418\u0440\u043a\u0443\u0442\u0441\u043a'), (4, '\u0421\u043b\u0430\u0442\u0430'), (9, '\u0412\u0430\u043b\u0442\u0430'), (6, '\u0414\u043e\u0433\u0421\u0435\u0440\u0432\u0438\u0441'), (7, '\u041a\u0440\u043e\u043d\u043e\u0441'), (8, '\u0422\u0430\u043e\u0411\u0430\u043e')], default=1, verbose_name='\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a'),
        ),
    ]
