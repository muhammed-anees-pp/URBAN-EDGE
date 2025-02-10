from django.urls import path
from .views import (
    place_order, order_success, 
    user_orders, user_order_details, cancel_order_item, 
    order_management, admin_order_details, update_order_status,
    request_return, download_invoice
)

urlpatterns = [
    path('checkout/', place_order, name='place_order'),
    path('order-success/', order_success, name='order_success'),
    path('my-orders/', user_orders, name='user_orders'),
    path('my-orders/<str:item_id>/', user_order_details, name='user_order_details'),
    path('cancel-order-item/<str:item_id>/', cancel_order_item, name='cancel_order_item'),
    path('request-return/<str:item_id>/', request_return, name='request_return'),
    path('admin/orders/', order_management, name='order_management'),
    path('admin/orders/<str:order_id>/', admin_order_details, name='admin_order_details'),
    path('admin/orders/<str:order_id>/update-status/', update_order_status, name='update_order_status'),
    path('download-invoice/<str:order_id>/', download_invoice, name='download_invoice'),
    
]