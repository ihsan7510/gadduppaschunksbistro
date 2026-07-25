from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    # Staff
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.staff_create, name='staff_create'),
    path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),
    path('staff/<int:pk>/delete/', views.staff_delete, name='staff_delete'),
    # Attendance
    path('attendance/', views.attendance, name='attendance'),
    path('attendance/<int:pk>/update/', views.attendance_update, name='attendance_update'),
    # Tables
    path('tables/', views.table_list, name='table_list'),
    path('tables/add/', views.table_create, name='table_create'),
    path('tables/<int:pk>/edit/', views.table_edit, name='table_edit'),
    path('tables/<int:pk>/delete/', views.table_delete, name='table_delete'),
    # Menu
    path('menu/', views.menu_list, name='menu_list'),
    path('menu/add/', views.menu_create, name='menu_create'),
    path('menu/<int:pk>/edit/', views.menu_edit, name='menu_edit'),
    path('menu/<int:pk>/delete/', views.menu_delete, name='menu_delete'),
    path('categories/', views.category_list, name='category_list'),
    # Inventory
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/add/', views.inventory_create, name='inventory_create'),
    path('inventory/<int:pk>/edit/', views.inventory_edit, name='inventory_edit'),
    path('inventory/<int:pk>/delete/', views.inventory_delete, name='inventory_delete'),
    # Billing
    path('billing/', views.billing_list, name='billing_list'),
    path('billing/<int:pk>/', views.bill_detail, name='bill_detail'),
    path('billing/<int:pk>/print/', views.bill_print, name='bill_print'),
    path('billing/<int:pk>/pay/', views.bill_mark_paid, name='bill_mark_paid'),
    # Settings
    path('settings/', views.settings_view, name='settings'),
    path('settings/scan-bluetooth/', views.scan_bluetooth, name='scan_bluetooth'),
]

