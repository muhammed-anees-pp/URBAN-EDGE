from django.urls import path
from .views import apply_coupon, remove_coupon

urlpatterns = [
    path('apply-coupon/', apply_coupon, name='apply_coupon'),
    path('remove-coupon/', remove_coupon, name='remove_coupon'),
]