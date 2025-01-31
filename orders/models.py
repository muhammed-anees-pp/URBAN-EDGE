# import uuid
# from django.db import models
# from django.contrib.auth.models import User
# from productsapp.models import Product, ProductVariant
# from user_profile.models import Address
# from django.utils import timezone

# def generate_order_id():
#     # Example: ORD-20231025-USER123-ABC123
#     date_part = timezone.now().strftime("%Y%m%d")  # Current date in YYYYMMDD format
#     random_part = uuid.uuid4().hex[:6].upper()  # Random 6-character string
#     return f"ORD-{date_part}-{random_part}"

# class Order(models.Model):
#     ORDER_STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('completed', 'Completed'),
#         ('canceled', 'Canceled'),
#     ]

#     id = models.CharField(primary_key=True, max_length=50, default=generate_order_id, editable=False)  # Custom order ID
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
#     payment_method = models.CharField(max_length=20)
#     total_price = models.DecimalField(max_digits=10, decimal_places=2)
#     status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default='pending')
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"Order #{self.id} - {self.user.username}"

# class OrderItem(models.Model):
#     order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     # product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)  # Add this line
#     product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
#     quantity = models.PositiveIntegerField()
#     price = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return f"{self.quantity} x {self.product.name}"


import uuid
from django.db import models
from django.contrib.auth.models import User
from productsapp.models import Product, ProductVariant
from user_profile.models import Address
from django.utils import timezone

def generate_order_id():
    # Example: ORD-20231025-USER123-ABC123
    date_part = timezone.now().strftime("%Y%m%d")  # Current date in YYYYMMDD format
    random_part = uuid.uuid4().hex[:6].upper()  # Random 6-character string
    return f"ORD-{date_part}-{random_part}"

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('order_placed', 'Order Placed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    ]

    id = models.CharField(primary_key=True, max_length=50, default=generate_order_id, editable=False)  # Custom order ID
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    payment_method = models.CharField(max_length=20)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='order_placed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

# class OrderItem(models.Model):
#     order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
#     quantity = models.PositiveIntegerField()
#     price = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return f"{self.quantity} x {self.product.name}"


class OrderItem(models.Model):
    ORDER_ITEM_STATUS_CHOICES = [
        ('order_placed', 'Order Placed'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out For Delivery'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
        ('return', 'Return'),
    ]

    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_ITEM_STATUS_CHOICES, default='order_placed')
    cancel_reason = models.TextField(blank=True, null=True)  # Add this field

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"