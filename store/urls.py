# store/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('books/', views.book_list, name='book_list'),
    path('book/<int:pk>/', views.book_detail, name='book_detail'),

    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:book_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:book_id>/', views.remove_from_cart, name='remove_from_cart'),

    path('checkout/', views.checkout, name='checkout'),
    path('payment/', views.payment_view, name='payment'),    
    path('payment-success/', views.payment_success, name='payment_success'),
    path('orders/magic/<str:token>/', views.order_magic_access, name='order_magic_access'),
]