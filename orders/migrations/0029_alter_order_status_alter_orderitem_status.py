# Generated by Django 5.1.5 on 2025-02-16 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0028_remove_order_coupon_discount_applied_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('processing', 'Processing'), ('pending', 'Pending'), ('completed', 'Completed'), ('canceled', 'Canceled'), ('returned', 'Returned')], default='processing', max_length=20),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='status',
            field=models.CharField(choices=[('processing', 'Processing'), ('order_placed', 'Order Placed'), ('shipped', 'Shipped'), ('out_for_delivery', 'Out For Delivery'), ('delivered', 'Delivered'), ('canceled', 'Canceled'), ('return_requested', 'Return Requested'), ('returned', 'Returned'), ('return', 'Return'), ('return_denied', 'Return Denied')], default='processing', max_length=20),
        ),
    ]
