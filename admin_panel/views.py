"""Admin Panel Views"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
import datetime

from core.models import (
    Staff, Attendance, RestaurantTable, Category, MenuItem,
    InventoryItem, Order, OrderItem, Bill, RestaurantSettings
)


def get_settings():
    obj, _ = RestaurantSettings.objects.get_or_create(pk=1)
    return obj


def admin_login(request):
    if request.session.get('admin_logged_in'):
        return redirect('admin_panel:dashboard')
    
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username == 'admin' and password == 'admin123':
            request.session['admin_logged_in'] = True
            return redirect('admin_panel:dashboard')
        else:
            error = 'Invalid credentials'
    
    return render(request, 'admin_panel/login.html', {'error': error})


def admin_logout(request):
    request.session.flush()
    return redirect('admin_panel:login')


def admin_required(view_func):
    """Decorator to require admin session."""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_logged_in'):
            return redirect('admin_panel:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def dashboard(request):
    today = timezone.now().date()
    
    # Stats
    total_tables = RestaurantTable.objects.count()
    free_tables = RestaurantTable.objects.filter(status='free').count()
    occupied_tables = RestaurantTable.objects.filter(status='occupied').count()
    
    active_orders = Order.objects.filter(
        status__in=['pending', 'confirmed', 'preparing', 'ready', 'served']
    ).count()
    
    today_bills = Bill.objects.filter(created_at__date=today, is_paid=True)
    today_revenue = today_bills.aggregate(total=Sum('total'))['total'] or 0
    today_orders = Order.objects.filter(created_at__date=today).count()
    
    staff_on_duty = Attendance.objects.filter(date=today, status='on_duty').count()
    
    # Low stock items
    low_stock_items = InventoryItem.objects.all()
    low_stock_count = sum(1 for item in low_stock_items if item.is_low_stock)
    
    # Recent orders
    recent_orders = Order.objects.select_related('table', 'waiter').order_by('-created_at')[:10]
    
    # Weekly revenue (last 7 days)
    weekly_data = []
    weekly_labels = []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        rev = Bill.objects.filter(created_at__date=day, is_paid=True).aggregate(
            total=Sum('total')
        )['total'] or 0
        weekly_data.append(float(rev))
        weekly_labels.append(day.strftime('%d %b'))
    
    context = {
        'total_tables': total_tables,
        'free_tables': free_tables,
        'occupied_tables': occupied_tables,
        'active_orders': active_orders,
        'today_revenue': today_revenue,
        'today_orders': today_orders,
        'staff_on_duty': staff_on_duty,
        'low_stock_count': low_stock_count,
        'recent_orders': recent_orders,
        'weekly_data': weekly_data,
        'weekly_labels': weekly_labels,
        'settings': get_settings(),
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ─────────────────────── STAFF ─────────────────────────
@admin_required
def staff_list(request):
    staff = Staff.objects.all()
    return render(request, 'admin_panel/staff_list.html', {'staff': staff, 'settings': get_settings()})


@admin_required
def staff_create(request):
    if request.method == 'POST':
        Staff.objects.create(
            name=request.POST['name'],
            role=request.POST['role'],
            phone=request.POST.get('phone', ''),
            pin=request.POST['pin'],
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, 'Staff member added successfully!')
        return redirect('admin_panel:staff_list')
    return render(request, 'admin_panel/staff_form.html', {
        'title': 'Add Staff', 'settings': get_settings(),
        'roles': Staff.ROLE_CHOICES
    })


@admin_required
def staff_edit(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        staff.name = request.POST['name']
        staff.role = request.POST['role']
        staff.phone = request.POST.get('phone', '')
        staff.pin = request.POST['pin']
        staff.is_active = request.POST.get('is_active') == 'on'
        staff.save()
        messages.success(request, 'Staff updated successfully!')
        return redirect('admin_panel:staff_list')
    return render(request, 'admin_panel/staff_form.html', {
        'title': 'Edit Staff', 'staff': staff, 'settings': get_settings(),
        'roles': Staff.ROLE_CHOICES
    })


@admin_required
def staff_delete(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        staff.delete()
        messages.success(request, 'Staff deleted.')
    return redirect('admin_panel:staff_list')


# ─────────────────────── ATTENDANCE ─────────────────────────
@admin_required
def attendance(request):
    today = timezone.now().date()
    date_str = request.GET.get('date', today.strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.date.fromisoformat(date_str)
    except ValueError:
        selected_date = today
    
    all_staff = Staff.objects.filter(is_active=True)
    attendance_records = {}
    for record in Attendance.objects.filter(date=selected_date).select_related('staff'):
        attendance_records[record.staff.pk] = record
    
    rows = []
    for s in all_staff:
        att = attendance_records.get(s.pk)
        rows.append({
            'staff': s,
            'record': att,
            'status': att.status if att else 'absent',
            'clock_in': att.clock_in if att else None,
            'clock_out': att.clock_out if att else None,
        })
    
    context = {
        'rows': rows,
        'selected_date': selected_date,
        'today': today,
        'settings': get_settings(),
    }
    return render(request, 'admin_panel/attendance.html', context)


@admin_required
def attendance_update(request, pk):
    if request.method == 'POST':
        staff = get_object_or_404(Staff, pk=pk)
        date_str = request.POST.get('date')
        date = datetime.date.fromisoformat(date_str)
        att, created = Attendance.objects.get_or_create(staff=staff, date=date)
        att.status = request.POST.get('status', 'absent')
        clock_in = request.POST.get('clock_in')
        clock_out = request.POST.get('clock_out')
        if clock_in:
            att.clock_in = clock_in
        if clock_out:
            att.clock_out = clock_out
        att.save()
        messages.success(request, f"Attendance updated for {staff.name}")
    return redirect(f'/admin-panel/attendance/?date={date_str}')


# ─────────────────────── TABLES ─────────────────────────
@admin_required
def table_list(request):
    tables = RestaurantTable.objects.all()
    return render(request, 'admin_panel/table_list.html', {'tables': tables, 'settings': get_settings()})


@admin_required
def table_create(request):
    if request.method == 'POST':
        RestaurantTable.objects.create(
            number=request.POST['number'],
            name=request.POST.get('name', ''),
            capacity=request.POST.get('capacity', 4),
            location=request.POST.get('location', ''),
        )
        messages.success(request, 'Table added!')
        return redirect('admin_panel:table_list')
    return render(request, 'admin_panel/table_form.html', {'title': 'Add Table', 'settings': get_settings()})


@admin_required
def table_edit(request, pk):
    table = get_object_or_404(RestaurantTable, pk=pk)
    if request.method == 'POST':
        table.number = request.POST['number']
        table.name = request.POST.get('name', '')
        table.capacity = request.POST.get('capacity', 4)
        table.location = request.POST.get('location', '')
        table.status = request.POST.get('status', 'free')
        table.save()
        messages.success(request, 'Table updated!')
        return redirect('admin_panel:table_list')
    return render(request, 'admin_panel/table_form.html', {
        'title': 'Edit Table', 'table': table, 'settings': get_settings(),
        'status_choices': RestaurantTable.STATUS_CHOICES
    })


@admin_required
def table_delete(request, pk):
    if request.method == 'POST':
        get_object_or_404(RestaurantTable, pk=pk).delete()
        messages.success(request, 'Table deleted.')
    return redirect('admin_panel:table_list')


# ─────────────────────── MENU ─────────────────────────
@admin_required
def menu_list(request):
    categories = Category.objects.prefetch_related('items').all()
    items = MenuItem.objects.select_related('category').all()
    return render(request, 'admin_panel/menu_list.html', {
        'categories': categories, 'items': items, 'settings': get_settings()
    })


@admin_required
def menu_create(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        item = MenuItem(
            name=request.POST['name'],
            category_id=request.POST['category'],
            price=request.POST['price'],
            description=request.POST.get('description', ''),
            is_available=request.POST.get('is_available') == 'on',
            is_veg=request.POST.get('is_veg') == 'on',
            preparation_time=request.POST.get('preparation_time', 15),
        )
        if 'image' in request.FILES:
            item.image = request.FILES['image']
        item.save()
        messages.success(request, 'Menu item added!')
        return redirect('admin_panel:menu_list')
    return render(request, 'admin_panel/menu_form.html', {
        'title': 'Add Menu Item', 'categories': categories, 'settings': get_settings()
    })


@admin_required
def menu_edit(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    categories = Category.objects.all()
    if request.method == 'POST':
        item.name = request.POST['name']
        item.category_id = request.POST['category']
        item.price = request.POST['price']
        item.description = request.POST.get('description', '')
        item.is_available = request.POST.get('is_available') == 'on'
        item.is_veg = request.POST.get('is_veg') == 'on'
        item.preparation_time = request.POST.get('preparation_time', 15)
        if 'image' in request.FILES:
            item.image = request.FILES['image']
        item.save()
        messages.success(request, 'Menu item updated!')
        return redirect('admin_panel:menu_list')
    return render(request, 'admin_panel/menu_form.html', {
        'title': 'Edit Menu Item', 'item': item, 'categories': categories, 'settings': get_settings()
    })


@admin_required
def menu_delete(request, pk):
    if request.method == 'POST':
        get_object_or_404(MenuItem, pk=pk).delete()
        messages.success(request, 'Menu item deleted.')
    return redirect('admin_panel:menu_list')


@admin_required
def category_list(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        Category.objects.create(
            name=request.POST['name'],
            icon=request.POST.get('icon', '🍽️'),
            sort_order=request.POST.get('sort_order', 0)
        )
        messages.success(request, 'Category added!')
        return redirect('admin_panel:category_list')
    return render(request, 'admin_panel/category_list.html', {
        'categories': categories, 'settings': get_settings()
    })


# ─────────────────────── INVENTORY ─────────────────────────
@admin_required
def inventory_list(request):
    items = InventoryItem.objects.all()
    low_stock = [i for i in items if i.is_low_stock]
    return render(request, 'admin_panel/inventory_list.html', {
        'items': items, 'low_stock': low_stock, 'settings': get_settings()
    })


@admin_required
def inventory_create(request):
    if request.method == 'POST':
        InventoryItem.objects.create(
            name=request.POST['name'],
            unit=request.POST['unit'],
            quantity=request.POST['quantity'],
            low_stock_threshold=request.POST.get('low_stock_threshold', 5),
            cost_per_unit=request.POST.get('cost_per_unit', 0),
            supplier=request.POST.get('supplier', ''),
        )
        messages.success(request, 'Inventory item added!')
        return redirect('admin_panel:inventory_list')
    return render(request, 'admin_panel/inventory_form.html', {
        'title': 'Add Inventory Item', 'units': InventoryItem.UNIT_CHOICES, 'settings': get_settings()
    })


@admin_required
def inventory_edit(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        item.name = request.POST['name']
        item.unit = request.POST['unit']
        item.quantity = request.POST['quantity']
        item.low_stock_threshold = request.POST.get('low_stock_threshold', 5)
        item.cost_per_unit = request.POST.get('cost_per_unit', 0)
        item.supplier = request.POST.get('supplier', '')
        item.save()
        messages.success(request, 'Inventory updated!')
        return redirect('admin_panel:inventory_list')
    return render(request, 'admin_panel/inventory_form.html', {
        'title': 'Edit Inventory Item', 'item': item,
        'units': InventoryItem.UNIT_CHOICES, 'settings': get_settings()
    })


@admin_required
def inventory_delete(request, pk):
    if request.method == 'POST':
        get_object_or_404(InventoryItem, pk=pk).delete()
        messages.success(request, 'Inventory item deleted.')
    return redirect('admin_panel:inventory_list')


# ─────────────────────── BILLING ─────────────────────────
@admin_required
def billing_list(request):
    bills = Bill.objects.select_related('order', 'order__table').order_by('-created_at')
    
    # Filters
    date_filter = request.GET.get('date')
    if date_filter:
        bills = bills.filter(created_at__date=date_filter)
    
    paid_filter = request.GET.get('paid')
    if paid_filter == 'yes':
        bills = bills.filter(is_paid=True)
    elif paid_filter == 'no':
        bills = bills.filter(is_paid=False)
    
    total_revenue = bills.filter(is_paid=True).aggregate(t=Sum('total'))['t'] or 0
    
    return render(request, 'admin_panel/billing_list.html', {
        'bills': bills, 'total_revenue': total_revenue,
        'settings': get_settings(), 'today': timezone.now().date()
    })


@admin_required
def bill_detail(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    return render(request, 'admin_panel/bill_detail.html', {
        'bill': bill, 'settings': get_settings()
    })


@admin_required
def bill_print(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    settings_obj = get_settings()
    from core.printer import print_bill, generate_receipt_text
    success, message = print_bill(bill, settings_obj)
    receipt_text = generate_receipt_text(bill, settings_obj)
    return render(request, 'admin_panel/bill_print.html', {
        'bill': bill, 'success': success, 'message': message,
        'receipt_text': receipt_text, 'settings': settings_obj
    })


@admin_required
def bill_mark_paid(request, pk):
    if request.method == 'POST':
        bill = get_object_or_404(Bill, pk=pk)
        bill.is_paid = True
        bill.paid_at = timezone.now()
        bill.payment_method = request.POST.get('payment_method', 'cash')
        bill.save()
        
        # Free table
        bill.order.table.status = 'free'
        bill.order.table.save()
        bill.order.status = 'billed'
        bill.order.save()
        
        messages.success(request, f"Bill #{bill.pk} marked as paid.")
    return redirect('admin_panel:billing_list')


# ─────────────────────── SETTINGS ─────────────────────────
@admin_required
def settings_view(request):
    obj = get_settings()
    if request.method == 'POST':
        obj.restaurant_name = request.POST.get('restaurant_name', obj.restaurant_name)
        obj.address = request.POST.get('address', '')
        obj.phone = request.POST.get('phone', '')
        obj.gstin = request.POST.get('gstin', '')
        obj.tax_percent = request.POST.get('tax_percent', 5)
        obj.printer_mac = request.POST.get('printer_mac', '')
        obj.printer_port = request.POST.get('printer_port', '')
        obj.footer_message = request.POST.get('footer_message', obj.footer_message)
        obj.currency_symbol = request.POST.get('currency_symbol', '₹')
        if 'logo' in request.FILES:
            obj.logo = request.FILES['logo']
        obj.save()
        messages.success(request, 'Settings saved successfully!')
        return redirect('admin_panel:settings')
    return render(request, 'admin_panel/settings.html', {'s': obj, 'settings': obj})
