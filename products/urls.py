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
    path('<int:product_id>',views.product_details,name='product_details'),
    path('category/<int:category_id>/', views.category_products, name='category_products'),
]