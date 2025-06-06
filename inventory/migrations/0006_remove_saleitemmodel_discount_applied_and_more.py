# Generated by Django 5.0 on 2025-05-25 17:37

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_site', '0007_schoolsettingmodel_use_barcode_scanner'),
        ('inventory', '0005_stockinmodel_stockinsummarymodel_stockoutmodel'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='saleitemmodel',
            name='discount_applied',
        ),
        migrations.RemoveField(
            model_name='saleitemmodel',
            name='tax_applied',
        ),
        migrations.RemoveField(
            model_name='salemodel',
            name='amount_paid',
        ),
        migrations.RemoveField(
            model_name='salemodel',
            name='change_due',
        ),
        migrations.RemoveField(
            model_name='salemodel',
            name='notes',
        ),
        migrations.RemoveField(
            model_name='salemodel',
            name='payment_method',
        ),
        migrations.AddField(
            model_name='saleitemmodel',
            name='cost_price',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=10, validators=[django.core.validators.MinValueValidator(0.0)]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='saleitemmodel',
            name='profit',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=10, validators=[django.core.validators.MinValueValidator(0.0)]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='salemodel',
            name='session',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_site.sessionmodel'),
        ),
        migrations.AddField(
            model_name='salemodel',
            name='term',
            field=models.CharField(blank=True, choices=[('1st term', '1st TERM'), ('2nd term', '2nd TERM'), ('3rd term', '3rd TERM')], max_length=10, null=True),
        ),
    ]
