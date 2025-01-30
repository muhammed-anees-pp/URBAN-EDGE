# from django.urls import path
# from .views import place_order, order_success

# urlpatterns = [
#     path('checkout/', place_order, name='place_order'),
#     path('order-success/', order_success, name='order_success'),
# ]

# from django.urls import path
# from .views import (
#     place_order, order_success, 
#     order_management, admin_order_details, update_order_status,
#     user_orders, user_order_details, cancel_order
# )

# urlpatterns = [
#     # Checkout and success page
#     path('checkout/', place_order, name='place_order'),
#     path('order-success/', order_success, name='order_success'),

#     # Admin order management
#     path('admin/orders/', order_management, name='order_management'),
#     path('admin/orders/<int:order_id>/', admin_order_details, name='admin_order_details'),
#     path('admin/orders/<int:order_id>/update-status/', update_order_status, name='update_order_status'),

#     # User order history
#     path('my-orders/', user_orders, name='user_orders'),
#     # path('my-orders/<str:order_id>/', user_order_details, name='user_order_details'),
#     path('my-orders/<int:order_id>/', user_order_details, name='user_order_details'),
#     path('my-orders/<int:order_id>/cancel/', cancel_order, name='cancel_order'),
# ]


from django.urls import path
from .views import (
    place_order, order_success, 
    order_management, admin_order_details, update_order_status,
    user_orders, user_order_details, cancel_order_item
)

urlpatterns = [
    # Checkout and success page
    path('checkout/', place_order, name='place_order'),
    path('order-success/', order_success, name='order_success'),

    # Admin order management
    path('admin/orders/', order_management, name='order_management'),
    path('admin/orders/<str:order_id>/', admin_order_details, name='admin_order_details'),
    path('admin/orders/<str:order_id>/update-status/', update_order_status, name='update_order_status'),

    # User order history
    path('my-orders/', user_orders, name='user_orders'),
    path('my-orders/<str:order_id>/', user_order_details, name='user_order_details'),
    path('my-orders/<str:order_id>/cancel/', cancel_order_item, name='cancel_order'),
]

