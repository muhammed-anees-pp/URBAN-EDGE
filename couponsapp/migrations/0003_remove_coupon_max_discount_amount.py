# Generated by Django 5.1.5 on 2025-02-15 16:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('couponsapp', '0002_coupon_max_discount_amount_alter_coupon_valid_from_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coupon',
            name='max_discount_amount',
        ),
    ]
