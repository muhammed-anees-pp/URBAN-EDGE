# Generated by Django 5.1.5 on 2025-02-05 07:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_alter_orderitem_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_status',
            field=models.CharField(default='pending', max_length=20),
        ),
    ]
