# Generated by Django 5.0 on 2025-05-26 04:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admin_site', '0007_schoolsettingmodel_use_barcode_scanner'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='schoolsettingmodel',
            name='use_barcode_scanner',
        ),
    ]
