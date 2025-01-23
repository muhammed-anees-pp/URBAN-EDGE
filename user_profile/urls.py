from django.urls import path
from . import views

urlpatterns = [
    path("user-profile/",views.user_profile,name='user_profile'),
    path("user-address/", views.view_addresses, name='addresses'),
    path('add-address/', views.add_address, name='add_address'),
    path('edit-address/', views.edit_address, name='edit_address'),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('change-password/', views.change_password, name='change_password'),
]