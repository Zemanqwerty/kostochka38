# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-29 19:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0018_item_temporarily_unavailable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deckitem',
            name='availability',
            field=models.IntegerField(choices=[(0, '\u041d\u0435\u0442 \u0432 \u043d\u0430\u043b\u0438\u0447\u0438\u0438'), (3, '\u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438 \u0443 \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0430'), (10, '\u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438 \u043d\u0430 \u0441\u043a\u043b\u0430\u0434\u0435')], default=3, verbose_name='\u041d\u0430\u043b\u0438\u0447\u0438\u0435 \u0442\u043e\u0432\u0430\u0440\u0430'),
        ),
        migrations.AlterField(
            model_name='item',
            name='availability',
            field=models.IntegerField(choices=[(0, '\u041d\u0435\u0442 \u0432 \u043d\u0430\u043b\u0438\u0447\u0438\u0438'), (3, '\u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438 \u0443 \u043f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a\u0430'), (10, '\u0412 \u043d\u0430\u043b\u0438\u0447\u0438\u0438 \u043d\u0430 \u0441\u043a\u043b\u0430\u0434\u0435')], default=3, verbose_name='\u041d\u0430\u043b\u0438\u0447\u0438\u0435 \u0442\u043e\u0432\u0430\u0440\u0430'),
        ),
    ]