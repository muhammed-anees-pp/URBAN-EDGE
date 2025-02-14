from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

class Coupon(models.Model):
    coupon_id = models.BigAutoField(primary_key=True)  # Ensure ID exists
    coupon_code = models.CharField(max_length=50, unique=True)
    minimum_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateField()
    valid_to = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.coupon_code

    def clean(self):
        # Ensure valid_from is not in the past
        if self.valid_from and self.valid_from < timezone.now().date():
            raise ValidationError({'valid_from': 'Valid from date cannot be in the past.'})

        # Ensure valid_to is after valid_from
        if self.valid_to and self.valid_from and self.valid_to <= self.valid_from:
            raise ValidationError({'valid_to': 'Valid to date must be after valid from date.'})

    def is_valid(self):
        now = timezone.now().date()
        return self.valid_from <= now <= self.valid_to and self.is_active


class CouponUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'coupon')

    def __str__(self):
        return f"{self.user.username} used {self.coupon.coupon_code}"