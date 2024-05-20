# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2020-08-20 14:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('campaign', '0007_auto_20190806_1020'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='campaign',
            options={'ordering': ('-id', 'sent'), 'permissions': (('send_campaign', 'Can send campaign'),), 'verbose_name': 'campaign', 'verbose_name_plural': 'campaigns'},
        ),
        migrations.AlterModelOptions(
            name='mailtemplate',
            options={'ordering': ('-id',), 'verbose_name': 'mail template', 'verbose_name_plural': 'mail templates'},
        ),
        migrations.AlterModelOptions(
            name='newsletter',
            options={'ordering': ('-id',), 'verbose_name': 'newsletter', 'verbose_name_plural': 'newsletters'},
        ),
    ]