
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('account/', include('accounts.urls')),
    path('adminpanel/', include('admin_side.urls')),
    path('category/', include('category.urls')),
    # path('auth/', include('social_django.urls', namespace='social')),
    # path('accounts/', include('allauth.urls')),
    # path('social-auth/', include('social_django.urls', namespace='social')),
    path('', include('user_profile.urls')),
    path('shop/', include('shop.urls')),
    path('products/',include('productsapp.urls')),
    path('cart/', include('cart.urls')),
]
urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)