from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import User_Details

@receiver(user_logged_in)
def update_user_details(sender, request, user, **kwargs):
    if not hasattr(user, 'user_details'):
        User_Details.objects.create(
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            email=user.email,
            user=user
        )
