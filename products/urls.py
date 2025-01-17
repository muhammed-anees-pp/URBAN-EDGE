# # from django.urls import path
# # from . import views
# # from django.conf import settings
# # from django.conf.urls.static import static

# # app_name = 'products' 

# # urlpatterns = [
# #     path('products-list/', views.product_list, name='product_list'),  # Correct name
# #     path('add-products/', views.add_product, name='add_product'),
# #     path('edit-products/<int:product_id>/', views.edit_product, name='edit_product'),
# #     path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
# #     path('products/user/', views.category_with_products, name='products_user'),
# #     path('<int:category_id>/', views.category_with_products, name='category_products'),

# # ]
# # if settings.DEBUG:
# #     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# from django.urls import path
# from . import views
# from django.conf import settings
# from django.conf.urls.static import static

# app_name = 'products'

# urlpatterns = [
#     # Admin views
#     path('products-list/', views.product_list, name='product_list'),
#     path('add-products/', views.add_product, name='add_product'),
#     path('edit-products/<int:product_id>/', views.edit_product, name='edit_product'),
#     path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
    
#     # User views
#     path('products/user/', views.category_with_products, name='products_user'),
#     path('category/<int:category_id>/', views.category_with_products, name='category_products'),
# ]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# # urlpatterns = [
# #     # Admin views
# #     path('products-list/', views.product_list, name='product_list'),
# #     path('add-products/', views.add_product, name='add_product'),
# #     path('edit-products/<int:product_id>/', views.edit_product, name='edit_product'),
# #     path('delete/<int:product_id>/', views.delete_product, name='delete_product'),

# #     # User views
# #     path('products/user/', views.category_with_products, name='products_user'),
# #     path('category/<int:category_id>/', views.category_with_products, name='category_products'),
# # ]

from django.urls import path
from . import views

urlpatterns = [
    path("management",views.product_list,name='product_management'),
    path("create",views.create_product,name='create_product'),
    path("edit/<product_id>",views.edit_product,name='edit_product'),
    path('variant/<int:product_id>/', views.variant_list, name='variant'),
    path('variant/add/<int:product_id>/', views.add_size_variants, name='add_variant'),
    path('variant/update/<int:variant_id>', views.update_variant, name='update_variant'),
    path('list/<int:product_id>',views.toggle_product_listing,name='list_unlist'),
    path('details/<int:product_id>',views.product_details,name='product_details')
]