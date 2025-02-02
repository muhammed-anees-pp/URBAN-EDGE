# # from django.urls import path
# # from . import views

# # urlpatterns = [
# #     path('product/<int:product_id>/review/', views.add_review, name='add_review'),
# #     path('review/<int:review_id>/edit/', views.edit_review, name='edit_review'),
# # ]

# from django.urls import path
# from . import views

# urlpatterns = [
#     path('product/<int:product_id>/review/', views.add_review, name='add_review'),
#     path('review/<int:review_id>/edit/', views.edit_review, name='edit_review'),
# ]

from django.urls import path
from . import views

urlpatterns = [
    path('add_review/<int:product_id>/', views.add_review, name='add_review'),
    path('edit_review/<int:review_id>/', views.edit_review, name='edit_review'),
]