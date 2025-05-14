from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import (index, catalog_home, add_to_cart, register_view, CustomLoginView, CustomLogoutView, CheckoutView,
                    category_flowers, decrease_quantity, increase_quantity, remove_from_cart, CartView, OrderConfirmationView,
                    ProfileView, reorder, OrderDetailView, cancel_order)

# Указываем пути к страницам приложения
urlpatterns = ([
    path('', index, name='shop_home'),
    path('catalog/', catalog_home, name='catalog_home'),
    path('register/', register_view, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(next_page='shop_home'), name='logout'),
    path('cart/', CartView.as_view(), name='cart'),
    path('add-to-cart/<int:flower_id>/', add_to_cart, name='add_to_cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-confirmation/<int:pk>/', OrderConfirmationView.as_view(), name='order_confirmation'),
    path('category/<int:category_id>/', category_flowers, name='category_flowers'),
    path('cart/decrease/<int:item_id>/', decrease_quantity, name='decrease_quantity'),
    path('cart/increase/<int:item_id>/', increase_quantity, name='increase_quantity'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('reorder/<int:order_id>/', reorder, name='reorder'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_details'),
    path('cancel-order/<int:order_id>/', cancel_order, name='cancel_order'),
]	+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))