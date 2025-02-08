from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from user_profile.models import Referral

@receiver(user_signed_up)
def create_referral_code_for_user(request, user, **kwargs):
    """
    Create a referral code for users who sign up.
    """
    Referral.objects.create(user=user)
    print(f"Referral code created for user: {user.username}")  # Debugging