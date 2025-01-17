# from django.urls import path
# from . import views

# urlpatterns = [
#     path('signup/', views.user_signup, name='user_signup'),
#     path('otp_verification/', views.otp_verification, name='otp_verification'),
#     path('resend_otp', views.resend_otp, name='resend_otp'),
#     path('login/', views.user_login, name='user_login'),
#     path('logout/', views.user_logout, name='user_logout'),

# ]

# urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.user_login, name='userlogin'),
    path("register/", views.register, name='register'),
    path('otp/<str:email>/', views.verify_otp, name='verify_otp'),
    path('logout/',views.user_logout,name='userlogout'),
    path('otp/resend/<str:email>/',views.resend_otp, name='resend_otp'),
]