# """
# URL configuration for urban_edge project.

# The `urlpatterns` list routes URLs to views. For more information please see:
#     https://docs.djangoproject.com/en/5.1/topics/http/urls/
# Examples:
# Function views
#     1. Add an import:  from my_app import views
#     2. Add a URL to urlpatterns:  path('', views.home, name='home')
# Class-based views
#     1. Add an import:  from other_app.views import Home
#     2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
# Including another URLconf
#     1. Import the include() function: from django.urls import include, path
#     2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
# """
# from django.contrib import admin
# from django.urls import path, include
# # from django.conf.urls.static import static
# # from django.conf import settings


# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('admins/', include('admin_side.urls')),
#     path('', include('home.urls')),  # Your home app URLs
#     path('accounts/', include('allauth.urls')),  # Include allauth URLs here
#     path('accounts/custom/', include('accounts.urls')),  # You can keep this for custom account views
#     path('', include('category.urls')),
#     path('', include('products.urls')),
# ]

# # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    # path('user/', include('UserAuth.urls')),
    # path('shop/', include('Shop.urls')),
    path('account/', include('accounts.urls')),
    path('adminpanel/', include('admin_side.urls')),
    path('category/', include('category.urls')),
    path('product/',include('products.urls')),
    # path('cart/',include('Cart.urls')),
    # path('checkout/',include('Order.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
]

urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)