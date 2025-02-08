
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('home.urls')),
    path('admin/', admin.site.urls),
    path('user/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('adminpanel/', include('admin_side.urls')),
    path('category/', include('category.urls')),
    path('', include('user_profile.urls')),
    path('shop/', include('shop.urls')),
    path('products/',include('productsapp.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('review/', include('reviews.urls')),
    path('wishlist/', include('wishlist.urls')),
    path('payments/', include('payments.urls')),
    path('coupons/', include('couponsapp.urls')),
    path('wallet/', include('wallet.urls')),

]
urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)