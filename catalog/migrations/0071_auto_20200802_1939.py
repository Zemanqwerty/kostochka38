# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2020-08-02 19:39
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0070_auto_20200801_1645'),
    ]

    operations = [
        migrations.AddField(
            model_name='movementofgoods',
            name='date_end',
            field=models.DateTimeField(blank=True, null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0438\u044f'),
        ),
        migrations.AlterField(
            model_name='leftitem',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.Item', verbose_name='\u0412\u0435\u0441/\u0422\u0438\u043f \u0442\u043e\u0432\u0430\u0440\u0430'),
        ),
        migrations.AlterField(
            model_name='leftitem',
            name='left',
            field=models.IntegerField(default=0, verbose_name='\u041e\u0441\u0442\u0430\u0442\u043e\u043a'),
        ),
        migrations.AlterField(
            model_name='leftitem',
            name='warehouse',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.WareHouse', verbose_name='\u0421\u043a\u043b\u0430\u0434'),
        ),
        migrations.AlterField(
            model_name='movementofgoods',
            name='courier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='\u041a\u0443\u0440\u044c\u0435\u0440'),
        ),
        migrations.AlterField(
            model_name='movementofgoods',
            name='courier_paid',
            field=models.BooleanField(verbose_name='\u041a\u0443\u0440\u044c\u0435\u0440 \u043e\u043f\u043b\u0430\u0447\u0435\u043d'),
        ),
        migrations.AlterField(
            model_name='movementofgoods',
            name='creation_date',
            field=models.DateField(auto_now_add=True, verbose_name='\u0414\u0430\u0442\u0430 \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f'),
        ),
        migrations.AlterField(
            model_name='movementofgoods',
            name='delivery_date',
            field=models.DateField(blank=True, null=True, verbose_name='\u0414\u0430\u0442\u0430 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438'),
        ),
        migrations.AlterField(
            model_name='movementofgoods',
            name='status',
            field=models.IntegerField(choices=[(0, '\u041d\u043e\u0432\u043e\u0435'), (3, '\u041f\u0435\u0440\u0435\u043c\u0435\u0449\u0435\u043d\u0438\u0435 \u0441\u043e\u0431\u0440\u0430\u043d\u043e'), (31, '\u041f\u0435\u0440\u0435\u043c\u0435\u0449\u0435\u043d\u0438\u0435 \u0443 \u043a\u0443\u0440\u044c\u0435\u0440\u0430'), (4, '\u041a\u0443\u0440\u044c\u0435\u0440 \u0432\u044b\u0435\u0445\u0430\u043b'), (5, '\u041f\u0435\u0440\u0435\u043c\u0435\u0449\u0435\u043d\u0438\u0435 \u0434\u043e\u0441\u0442\u0430\u0432\u043b\u0435\u043d\u043e'), (6, '\u0417\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u043e'), (10, '\u041e\u0442\u043c\u0435\u043d\u0435\u043d\u043e')], default=0, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441'),
        ),
        migrations.AlterField(
            model_name='movementofgoods',
            name='warehouse_donor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='warehouse_giving', to='catalog.WareHouse', verbose_name='\u0421\u043a\u043b\u0430\u0434-\u043e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u0435\u043b\u044c'),
        ),
        migrations.AlterField(
            model_name='movementofgoods',
            name='warehouse_recieving',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='warehouse_recieving', to='catalog.WareHouse', verbose_name='\u0421\u043a\u043b\u0430\u0434-\u043f\u043e\u043b\u0443\u0447\u0430\u0442\u0435\u043b\u044c'),
        ),
        migrations.AlterField(
            model_name='movementstatuslog',
            name='status',
            field=models.IntegerField(choices=[(0, '\u041d\u043e\u0432\u043e\u0435'), (3, '\u041f\u0435\u0440\u0435\u043c\u0435\u0449\u0435\u043d\u0438\u0435 \u0441\u043e\u0431\u0440\u0430\u043d\u043e'), (31, '\u041f\u0435\u0440\u0435\u043c\u0435\u0449\u0435\u043d\u0438\u0435 \u0443 \u043a\u0443\u0440\u044c\u0435\u0440\u0430'), (4, '\u041a\u0443\u0440\u044c\u0435\u0440 \u0432\u044b\u0435\u0445\u0430\u043b'), (5, '\u041f\u0435\u0440\u0435\u043c\u0435\u0449\u0435\u043d\u0438\u0435 \u0434\u043e\u0441\u0442\u0430\u0432\u043b\u0435\u043d\u043e'), (6, '\u0417\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u043e'), (10, '\u041e\u0442\u043c\u0435\u043d\u0435\u043d\u043e')], default=0, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441'),
        ),
        migrations.AlterField(
            model_name='warehouse',
            name='address',
            field=models.CharField(blank=True, max_length=250, null=True, verbose_name='\u0410\u0434\u0440\u0435\u0441'),
        ),
        migrations.AlterField(
            model_name='warehouse',
            name='full_name',
            field=models.TextField(blank=True, null=True, verbose_name='\u041f\u043e\u043b\u043d\u043e\u0435 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u0435'),
        ),
        migrations.AlterField(
            model_name='warehouse',
            name='name',
            field=models.CharField(max_length=250, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435 \u0441\u043a\u043b\u0430\u0434\u0430'),
        ),
        migrations.AlterField(
            model_name='warehouse',
            name='phone',
            field=models.CharField(blank=True, max_length=250, null=True, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430'),
        ),
        migrations.AlterField(
            model_name='warehouse',
            name='type',
            field=models.IntegerField(choices=[(0, '\u0421\u043a\u043b\u0430\u0434'), (1, '\u0420\u043e\u0437\u043d\u0438\u0446\u0430')], default=0, verbose_name='\u0422\u0438\u043f \u0441\u043a\u043b\u0430\u0434\u0430'),
        ),
        migrations.AlterField(
            model_name='warehouse',
            name='working_mode_end',
            field=models.TimeField(blank=True, null=True, verbose_name='\u041a\u043e\u0435\u043d\u0446 \u0440\u0430\u0431\u043e\u0442\u044b'),
        ),
        migrations.AlterField(
            model_name='warehouse',
            name='working_mode_start',
            field=models.TimeField(blank=True, null=True, verbose_name='\u041d\u0430\u0447\u0430\u043b\u043e \u0440\u0430\u0431\u043e\u0442\u044b'),
        ),
    ]
