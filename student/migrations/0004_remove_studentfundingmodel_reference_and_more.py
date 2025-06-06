# Generated by Django 5.0 on 2025-05-24 06:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_site', '0006_alter_teachermodel_gender'),
        ('student', '0003_studentfundingmodel_method_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentfundingmodel',
            name='reference',
        ),
        migrations.AddField(
            model_name='studentfundingmodel',
            name='mode',
            field=models.CharField(blank=True, choices=[('offline', 'OFFLINE'), ('online', 'ONLINE')], default='offline', max_length=100),
        ),
        migrations.AddField(
            model_name='studentfundingmodel',
            name='session',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_site.sessionmodel'),
        ),
        migrations.AddField(
            model_name='studentfundingmodel',
            name='term',
            field=models.CharField(blank=True, choices=[('1st term', '1st TERM'), ('2nd term', '2nd TERM'), ('3rd term', '3rd TERM')], max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='studentfundingmodel',
            name='method',
            field=models.CharField(blank=True, choices=[('cash', 'CASH'), ('pos', 'POS'), ('bank teller', 'BANK TELLER'), ('bank transfer', 'BANK TRANSFER')], default='cash', max_length=100),
        ),
        migrations.AlterField(
            model_name='studentfundingmodel',
            name='status',
            field=models.CharField(blank=True, default='confirmed', max_length=30),
        ),
    ]
