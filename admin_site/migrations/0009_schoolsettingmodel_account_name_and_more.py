# Generated by Django 5.0 on 2025-05-28 05:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_site', '0008_remove_schoolsettingmodel_use_barcode_scanner'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolsettingmodel',
            name='account_name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='schoolsettingmodel',
            name='account_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='schoolsettingmodel',
            name='bank',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
