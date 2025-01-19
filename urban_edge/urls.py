
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
    # path('auth/', include('social_django.urls', namespace='social')),
    # path('accounts/', include('allauth.urls')),
    # path('social-auth/', include('social_django.urls', namespace='social')),
]
urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)