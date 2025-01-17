# # from django.db import models
# # from category.models import Category

# # # Create your models here.

# # class Product(models.Model):
# #     name = models.CharField(max_length=250)
# #     category= models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
# #     size = models.CharField(max_length=4)
# #     price = models.DecimalField(max_digits=10, decimal_places=2)
# #     stock = models.PositiveIntegerField()
# #     descriptioin = models.TextField(blank=True, null=True)
# #     # brand = models.CharField(max_length=200, blank=True, null=True)
# #     colors = models.JSONField(default=list, blank=True, null=True)
# #     image1 = models.ImageField(upload_to='products/', blank=True, null=True)
# #     image2 = models.ImageField(upload_to='products/', blank=True, null=True)
# #     image3 = models.ImageField(upload_to='products/', blank=True, null=True)
# #     is_active = models.BooleanField(default=True)

# #     def __str__(self):
# #         return self.name

# from django.db import models
# from category.models import Category

# # Predefined size options
# SIZE_CHOICES = [
#     ('XS', 'Extra Small'),
#     ('S', 'Small'),
#     ('M', 'Medium'),
#     ('L', 'Large'),
#     ('XL', 'Extra Large'),
#     ('XXL', 'Double Extra Large'),
# ]

# class Product(models.Model):
#     name = models.CharField(max_length=250)
#     category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
#     size = models.CharField(
#         max_length=10,
#         choices=SIZE_CHOICES,
#         blank=True,
#         null=True,
#         help_text="Select a predefined size or leave blank to use custom sizes."
#     )
#     custom_size = models.CharField(
#         max_length=10,
#         blank=True,
#         null=True,
#         help_text="Enter custom size (e.g., 41, 42) if predefined sizes do not apply."
#     )
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     stock = models.PositiveIntegerField()
#     description = models.TextField(blank=True, null=True)
#     # brand = models.CharField(max_length=200, blank=True, null=True)
#     colors = models.JSONField(default=list, blank=True, null=True)
#     image1 = models.ImageField(upload_to='products/', blank=True, null=True)
#     image2 = models.ImageField(upload_to='products/', blank=True, null=True)
#     image3 = models.ImageField(upload_to='products/', blank=True, null=True)
#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return self.name

from django.db import models
from category.models import Category

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()  
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=7, decimal_places=2)  # Adjusted precision
    offer = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)  # Increased precision
    color = models.CharField(max_length=50, null=True, blank=True)
    image1 = models.ImageField(upload_to='products/', null=True)
    image2 = models.ImageField(upload_to='products/', null=True, blank=True)
    image3 = models.ImageField(upload_to='products/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_listed = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class SizeVariant(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='size_variants')
    size = models.CharField(max_length=50)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.size}"