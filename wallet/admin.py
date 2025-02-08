from django.contrib import admin

# Register your models here.
from . models import Wallet, WalletTransaction

admin.site.register(Wallet)
admin.site.register(WalletTransaction)