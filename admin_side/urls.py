from django.urls import path
from . import views

urlpatterns = [
    path('admin-login/', views.admin_login, name='admin_login'),  # Admin login page
    path('dashboard/', views.dashboard, name='dashboard'),  # Dashboard page
    path('logout/', views.admin_logout, name='admin_logout'),  # Logout
]
