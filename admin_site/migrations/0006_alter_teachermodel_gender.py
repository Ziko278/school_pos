# Generated by Django 5.0 on 2025-05-23 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_site', '0005_teachermodel_classsectioninfomodel_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teachermodel',
            name='gender',
            field=models.CharField(choices=[('male', 'MALE'), ('female', 'FEMALE')], max_length=10),
        ),
    ]
