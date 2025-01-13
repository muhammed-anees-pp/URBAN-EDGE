from django.urls import path
from . import views

urlpatterns = [
    path('category-list/', views.category_list, name='category_list'),
    path('add-category/', views.add_category, name='add_category'),
    path('edit-category/<int:pk>/', views.edit_category, name='edit_category'),
    path('categories-delete/<int:pk>/', views.delete_category, name='delete_category'),
]