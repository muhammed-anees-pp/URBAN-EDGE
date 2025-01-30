from django.urls import path
from .views import place_order, order_success

urlpatterns = [
    path('checkout/', place_order, name='place_order'),
    path('order-success/', order_success, name='order_success'),
]
