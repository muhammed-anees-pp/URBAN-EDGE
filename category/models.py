# from django.db import models

# class Category(models.Model):
#     name = models.CharField(max_length=100, unique=True)
#     description = models.TextField(blank=True, null=True)
#     image = models.ImageField(upload_to='category_images/', blank=True, null=True)
#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return self.name
    
#     class Meta:
#         verbose_name_plural = 'categories'

from django.db import models

class Category(models.Model):
    category_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_listed = models.BooleanField(default=False)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True) 
    def __str__(self):
        return self.category_name