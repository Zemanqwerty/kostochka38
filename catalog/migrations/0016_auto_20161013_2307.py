# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-13 23:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0015_tempzakazgoods_sale'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProducerCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=512, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
            ],
            options={
                'ordering': ['title'],
                'verbose_name': '\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0438\u0442\u0435\u043b\u0435\u0439',
                'verbose_name_plural': '\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438 \u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0438\u0442\u0435\u043b\u0435\u0439',
            },
        ),
        migrations.AlterModelOptions(
            name='itemsale',
            options={'ordering': ['date_end'], 'verbose_name': '\u0421\u043a\u0438\u0434\u043a\u0430 \u043d\u0430 \u0442\u043e\u0432\u0430\u0440', 'verbose_name_plural': '\u0421\u043a\u0438\u0434\u043a\u0438 \u043d\u0430 \u0442\u043e\u0432\u0430\u0440'},
        ),
        migrations.AddField(
            model_name='producer',
            name='producercategory',
            field=models.ManyToManyField(blank=True, null=True, to='catalog.ProducerCategory', verbose_name='\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438'),
        ),
    ]
