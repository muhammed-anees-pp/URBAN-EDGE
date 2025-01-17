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