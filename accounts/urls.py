from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.user_signup, name='user_signup'),
    path('otp_verification/', views.otp_verification, name='otp_verification'),
    path('resend_otp', views.resend_otp, name='resend_otp'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),

]
