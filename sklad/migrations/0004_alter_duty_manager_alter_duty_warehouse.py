# Generated by Django 4.2.11 on 2024-03-25 13:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0108_alter_commentitem_status_alter_courier_name_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sklad', '0003_auto_20201110_2137'),
    ]

    operations = [
        migrations.AlterField(
            model_name='duty',
            name='manager',
            field=models.ForeignKey(limit_choices_to={'groups__id': '3'}, on_delete=django.db.models.deletion.CASCADE, related_name='sklad_dury_manager', to=settings.AUTH_USER_MODEL, verbose_name='Кладовщик'),
        ),
        migrations.AlterField(
            model_name='duty',
            name='warehouse',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='sklad_durt_warehouse', to='catalog.warehouse', verbose_name='Склад'),
        ),
    ]
