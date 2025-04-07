from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]

urlpatterns += [
    path('vendor/products/', views.vendor_products, name='vendor_products'),
    path('vendor/products/add/', views.add_product, name='add_product'),
    path('vendor/products/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('vendor/products/delete/<int:pk>/', views.delete_product, name='delete_product'),
]

urlpatterns += [
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:cart_id>/', views.remove_from_cart, name='remove_from_cart'),
]

urlpatterns += [
    path('checkout/', views.checkout, name='checkout'),
]

urlpatterns += [
    path('orders/history/', views.order_history, name='order_history'),
]

urlpatterns += [
    path('vendor/orders/', views.vendor_orders, name='vendor_orders'),
]

urlpatterns += [
    path('payment/success/', views.payment_success, name='payment_success'),
]

urlpatterns += [
    path('vendor/order/update/<int:order_id>/', views.update_order_status, name='update_order_status'),
]

urlpatterns += [
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/password/', auth_views.PasswordChangeView.as_view(template_name='core/change_password.html'), name='change_password'),
    path('profile/password/done/', auth_views.PasswordChangeDoneView.as_view(template_name='core/change_password_done.html'), name='password_change_done'),
]

urlpatterns += [
    path('review/<int:product_id>/', views.leave_review, name='leave_review'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

]