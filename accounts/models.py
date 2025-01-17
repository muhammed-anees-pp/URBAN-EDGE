# from django.db import models
# from django.contrib.auth.models import User

# class User_Details(models.Model):
#     first_name=models.CharField(max_length=50)
#     last_name=models.CharField(max_length=50)
#     username=models.CharField(max_length=50)
#     email=models.CharField(max_length=30)
#     password=models.CharField(max_length=100)
#     user=models.OneToOneField(User,null=True,on_delete=models.CASCADE)
#     is_active=models.BooleanField(default=True)

from django.db import models
from django.utils import timezone

class OTP(models.Model):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  

    def is_expired(self):
        return timezone.now() > self.expires_at