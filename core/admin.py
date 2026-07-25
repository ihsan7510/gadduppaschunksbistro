from django.contrib import admin
from .models import (
    Staff, Attendance, RestaurantTable, Category, MenuItem,
    InventoryItem, Order, OrderItem, Bill, RestaurantSettings
)


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'phone', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['name', 'phone']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['staff', 'date', 'clock_in', 'clock_out', 'status']
    list_filter = ['status', 'date']


@admin.register(RestaurantTable)
class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'name', 'capacity', 'status', 'location']
    list_filter = ['status']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'sort_order']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_available', 'is_veg']
    list_filter = ['category', 'is_available', 'is_veg']
    search_fields = ['name']


@admin.register(InventoryItem)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'quantity', 'unit', 'low_stock_threshold', 'is_low_stock']
    list_filter = ['unit']

    @admin.display(boolean=True, description='Low Stock?')
    def is_low_stock(self, obj):
        return obj.is_low_stock


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'table', 'waiter', 'status', 'created_at']
    list_filter = ['status']
    inlines = [OrderItemInline]


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['order', 'subtotal', 'tax_amount', 'discount_amount', 'total', 'payment_method', 'is_paid']
    list_filter = ['is_paid', 'payment_method']


@admin.register(RestaurantSettings)
class RestaurantSettingsAdmin(admin.ModelAdmin):
    pass
