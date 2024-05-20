# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-26 19:57
from __future__ import unicode_literals

import ckeditor_uploader.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0016_auto_20161013_2307'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='last_order_date',
            field=models.DateField(blank=True, null=True, verbose_name='\u041f\u043e\u0441\u043b\u0435\u0434\u043d\u044f\u044f \u043f\u0440\u043e\u0434\u0430\u0436\u0430'),
        ),
        migrations.AlterField(
            model_name='deckitem',
            name='composition',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True, verbose_name='\u0412\u0442\u043e\u0440\u043e\u0439 \u0431\u043b\u043e\u043a'),
        ),
        migrations.AlterField(
            model_name='deckitem',
            name='description',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435'),
        ),
        migrations.AlterField(
            model_name='deckitem',
            name='ration',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True, verbose_name='\u0422\u0440\u0435\u0442\u0438\u0439 \u0431\u043b\u043e\u043a'),
        ),
        migrations.AlterField(
            model_name='producer',
            name='producercategory',
            field=models.ManyToManyField(to='catalog.ProducerCategory', verbose_name='\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438'),
        ),
    ]