# from django.urls import path
# from . import views

# urlpatterns = [
#     path('signup/', views.signup, name='signup'),
#     path('verify_email/<str:email>/', views.verify_email, name='verify_email'),
#     path('login/', views.login_view, name='login'),
#     path('home/', views.home, name='home'),
# ]

# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('verify_email/<str:email>/', views.verify_email, name='verify_email'),
    path('login/', views.login_view, name='login'),
    path('home/', views.home, name='home'),
]
