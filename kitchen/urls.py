from django.urls import path
from . import views

app_name = 'kitchen'

urlpatterns = [
    path('', views.orders, name='orders'),
    path('login/', views.kitchen_login, name='login'),
    path('orders/', views.orders, name='orders'),
    path('orders/history/', views.order_history, name='order_history'),
    path('items/<int:item_pk>/status/', views.update_item_status, name='update_item_status'),
    path('orders/<int:order_pk>/complete/', views.complete_order, name='complete_order'),
]
