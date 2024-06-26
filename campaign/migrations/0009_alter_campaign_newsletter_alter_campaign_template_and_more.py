# Generated by Django 4.2.11 on 2024-03-25 13:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('campaign', '0008_auto_20200820_1417'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='newsletter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='campaign.newsletter', verbose_name='Newsletter'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='campaign.mailtemplate', verbose_name='Template'),
        ),
        migrations.AlterField(
            model_name='subscriberlist',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
    ]
