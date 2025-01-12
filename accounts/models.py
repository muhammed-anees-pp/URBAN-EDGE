from django.db import models
from django.contrib.auth.models import User

class User_Details(models.Model):
    first_name=models.CharField(max_length=50)
    last_name=models.CharField(max_length=50)
    username=models.CharField(max_length=50)
    email=models.CharField(max_length=30)
    password=models.CharField(max_length=100)
    user=models.OneToOneField(User,null=True,on_delete=models.CASCADE)
    is_active=models.BooleanField(default=True)