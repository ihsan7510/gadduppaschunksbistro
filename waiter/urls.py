from django.urls import path
from . import views

app_name = 'waiter'

urlpatterns = [
    path('', views.tables, name='tables'),
    path('login/', views.waiter_login, name='login'),
    path('logout/', views.waiter_logout, name='logout'),
    path('tables/', views.tables, name='tables'),
    path('tables/<int:table_pk>/order/', views.take_order, name='take_order'),
    path('parcels/new/', views.create_parcel_order, name='create_parcel_order'),
    path('tables/<int:table_pk>/place-order/', views.place_order, name='place_order'),
    path('orders/<int:order_pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_pk>/bill/', views.generate_bill, name='generate_bill'),
    path('orders/<int:order_pk>/cancel/', views.cancel_order, name='cancel_order'),
    path('orders/<int:order_pk>/serve/', views.mark_order_served, name='mark_served'),
    path('bills/<int:bill_pk>/print/', views.print_bill, name='print_bill'),
    path('bills/<int:bill_pk>/pay/', views.mark_paid, name='mark_paid'),
    path('bills/<int:bill_pk>/pay-quick/', views.pay_quick, name='pay_quick'),
]
