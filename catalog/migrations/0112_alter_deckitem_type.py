# Generated by Django 3.2.25 on 2024-05-07 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0111_auto_20240506_1928'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deckitem',
            name='type',
            field=models.CharField(blank=True, choices=[('dry', 'Сухой'), ('additional', 'Добавка'), ('wet', 'Влажный')], max_length=16, null=True, verbose_name='Тип'),
        ),
    ]