from django.db import models
from django.contrib.auth.models import User

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50, default='Kerala')
    country = models.CharField(max_length=100, default='India')
    postcode = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    is_deleted = models.BooleanField(default=False)
    additional_info = models.TextField(blank=True, null=True) 


    def __str__(self):
        return f"{self.name} - {self.address}, {self.city}, {self.state},{self.country}"