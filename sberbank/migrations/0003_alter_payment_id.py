# Generated by Django 3.2.25 on 2024-05-02 01:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sberbank', '0002_alter_banklog_request_type_alter_payment_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
