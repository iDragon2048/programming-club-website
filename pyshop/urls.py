from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='shop'),
    path('product/<pk>/', views.product_detail, name='product_detail'),
    path('add/<pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='cart'),
    path('remove/<pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('update_cart_item/<pk>', views.update_cart_item, name='update_cart_item'),
]