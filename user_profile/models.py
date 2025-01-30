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
    is_default = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    additional_info = models.TextField(blank=True, null=True) 


    def __str__(self):
        return f"{self.name} \n{self.address}, {self.city} \n{self.state},{self.country},{self.postcode} \nPhone: {self.phone}\n Email: {self.email}"
    

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super(Address, self).save(*args, **kwargs)

# Ensure there is one default address per user
def set_default_address(sender, instance, **kwargs):
    if instance.is_default:
        Address.objects.filter(user=instance.user).exclude(pk=instance.pk).update(is_default=False)

models.signals.pre_save.connect(set_default_address, sender=Address)