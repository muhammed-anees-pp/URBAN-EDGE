from django.urls import path
from .views import (
    apply_coupon, remove_coupon, coupon_list, add_coupon,
    edit_coupon, toggle_coupon_status, delete_coupon
)

urlpatterns = [
    path('apply-coupon/', apply_coupon, name='apply_coupon'),
    path('remove-coupon/', remove_coupon, name='remove_coupon'),
    path('admin/coupons/', coupon_list, name='coupon_list'),
    path('admin/coupons/add/', add_coupon, name='add_coupon'),
    path('admin/coupons/edit/<int:coupon_id>/', edit_coupon, name='edit_coupon'),
    path('admin/coupons/toggle-status/<int:coupon_id>/', toggle_coupon_status, name='toggle_coupon_status'),
    path('admin/coupons/delete/<int:coupon_id>/', delete_coupon, name='delete_coupon'),
]