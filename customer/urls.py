from django.urls import path
from . import views

app_name = 'customer'

urlpatterns = [
    path('table/<int:table_number>/', views.table_order, name='table_order'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-status/', views.order_status, name='order_status'),
]
