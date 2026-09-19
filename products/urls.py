from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/<str:action>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('orders/', views.order_history, name='order_history'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('about/', views.about_us, name='about_us'),
    path('order/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('order/return/<int:order_id>/', views.return_order, name='return_order'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/update/<int:order_id>/<str:new_status>/', views.update_order_status, name='update_order_status'),
    path('dashboard/delete/<int:order_id>/', views.delete_order, name='delete_order'),
    path('staff-login/', views.staff_login, name='staff_login'),
    path('dashboard/products/', views.manage_products, name='manage_products'),
    path('dashboard/products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('dashboard/categories/', views.manage_categories, name='manage_categories'),
    path('dashboard/categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    
]
