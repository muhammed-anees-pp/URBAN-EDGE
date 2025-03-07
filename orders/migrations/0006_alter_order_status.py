# Generated by Django 5.1.5 on 2025-01-31 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_orderitem_cancel_reason_orderitem_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('order_placed', 'Order Placed'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('canceled', 'Canceled')], default='order_placed', max_length=20),
        ),
    ]
