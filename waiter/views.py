"""Waiter Module Views"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
import json

from core.models import (
    Staff, RestaurantTable, Category, MenuItem, Order, OrderItem, Bill, RestaurantSettings
)


def get_settings():
    obj, _ = RestaurantSettings.objects.get_or_create(pk=1)
    return obj


def waiter_login(request):
    if request.session.get('waiter_id'):
        return redirect('waiter:tables')
    
    error = None
    if request.method == 'POST':
        pin = request.POST.get('pin', '').strip()
        try:
            staff = Staff.objects.get(pin=pin, is_active=True, role__in=['waiter', 'admin', 'cashier'])
            request.session['waiter_id'] = staff.pk
            request.session['waiter_name'] = staff.name
            request.session['waiter_role'] = staff.role
            
            # Mark attendance
            today = timezone.now().date()
            from core.models import Attendance
            att, created = Attendance.objects.get_or_create(staff=staff, date=today)
            if created or att.status == 'absent':
                att.status = 'on_duty'
                att.clock_in = timezone.now().time()
                att.save()
            
            return redirect('waiter:tables')
        except Staff.DoesNotExist:
            error = 'Invalid PIN. Please try again.'
    
    return render(request, 'waiter/login.html', {'error': error, 'settings': get_settings()})


def waiter_logout(request):
    waiter_id = request.session.get('waiter_id')
    if waiter_id:
        try:
            staff = Staff.objects.get(pk=waiter_id)
            today = timezone.now().date()
            from core.models import Attendance
            att, _ = Attendance.objects.get_or_create(staff=staff, date=today)
            att.clock_out = timezone.now().time()
            att.status = 'present'
            att.save()
        except Staff.DoesNotExist:
            pass
    request.session.flush()
    return redirect('waiter:login')


def waiter_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('waiter_id') and not request.session.get('admin_logged_in'):
            return redirect('waiter:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@waiter_required
def tables(request):
    all_tables = RestaurantTable.objects.filter(is_parcel=False).order_by('number')
    parcel_tables = RestaurantTable.objects.filter(is_parcel=True).exclude(status='free').order_by('number')
    
    # Annotate with active order info and existing bill
    table_data = []
    for table in all_tables:
        active_order = table.orders.filter(
            status__in=['pending', 'confirmed', 'preparing', 'ready', 'served', 'billed']
        ).first()
        # Check for an unpaid bill on this order
        bill_pk = None
        if active_order:
            try:
                if not active_order.bill.is_paid:
                    bill_pk = active_order.bill.pk
            except Exception:
                pass
        table_data.append({
            'table': table,
            'active_order': active_order,
            'bill_pk': bill_pk,
        })
    
    parcel_data = []
    for table in parcel_tables:
        active_order = table.orders.filter(
            status__in=['pending', 'confirmed', 'preparing', 'ready', 'served', 'billed']
        ).first()
        # Check for an unpaid bill on this order
        bill_pk = None
        if active_order:
            try:
                if not active_order.bill.is_paid:
                    bill_pk = active_order.bill.pk
            except Exception:
                pass
        parcel_data.append({
            'table': table,
            'active_order': active_order,
            'bill_pk': bill_pk,
        })
    
    context = {
        'table_data': table_data,
        'parcel_data': parcel_data,
        'waiter_name': request.session.get('waiter_name'),
        'settings': get_settings(),
    }
    return render(request, 'waiter/tables.html', context)


@waiter_required
def create_parcel_order(request):
    # Find a free parcel table or create a new one
    parcel_table = RestaurantTable.objects.filter(is_parcel=True, status='free').first()
    if not parcel_table:
        parcel_tables = RestaurantTable.objects.filter(is_parcel=True)
        if parcel_tables.exists():
            next_num = max(t.number for t in parcel_tables) + 1
        else:
            next_num = 100
        parcel_table = RestaurantTable.objects.create(
            number=next_num,
            capacity=1,
            status='free',
            is_parcel=True,
            location='Takeaway'
        )
    return redirect('waiter:take_order', table_pk=parcel_table.pk)


@waiter_required
def take_order(request, table_pk):
    table = get_object_or_404(RestaurantTable, pk=table_pk)
    categories = Category.objects.prefetch_related('items').filter(items__is_available=True).distinct()
    
    # Check for existing active order
    active_order = table.orders.filter(
        status__in=['pending', 'confirmed', 'preparing', 'ready', 'served']
    ).first()
    
    context = {
        'table': table,
        'categories': categories,
        'active_order': active_order,
        'waiter_name': request.session.get('waiter_name'),
        'settings': get_settings(),
    }
    return render(request, 'waiter/take_order.html', context)


@waiter_required
def place_order(request, table_pk):
    if request.method != 'POST':
        return redirect('waiter:take_order', table_pk=table_pk)
    
    table = get_object_or_404(RestaurantTable, pk=table_pk)
    waiter_id = request.session.get('waiter_id')
    if waiter_id:
        waiter = get_object_or_404(Staff, pk=waiter_id)
    else:
        waiter = Staff.objects.filter(role='admin').first()
        if not waiter:
            waiter, _ = Staff.objects.get_or_create(
                name="Admin",
                defaults={"role": "admin", "pin": "0000"}
            )
    
    # Check for existing active order or create new
    active_order = table.orders.filter(
        status__in=['pending', 'confirmed', 'preparing']
    ).first()
    
    if not active_order:
        active_order = Order.objects.create(
            table=table,
            waiter=waiter,
            status='confirmed',
            notes=request.POST.get('order_notes', ''),
        )
        table.status = 'occupied'
        table.save()
    
    # Add items from POST data
    items_added = 0
    for key, value in request.POST.items():
        if key.startswith('qty_'):
            menu_item_id = key.replace('qty_', '')
            qty = int(value)
            if qty > 0:
                try:
                    menu_item = MenuItem.objects.get(pk=menu_item_id, is_available=True)
                    note_key = f'note_{menu_item_id}'
                    note = request.POST.get(note_key, '')
                    OrderItem.objects.create(
                        order=active_order,
                        menu_item=menu_item,
                        quantity=qty,
                        price=menu_item.price,
                        notes=note,
                        status='pending',
                    )
                    items_added += 1
                except MenuItem.DoesNotExist:
                    pass
    
    # Notify kitchen via WebSocket
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    channel_layer = get_channel_layer()
    try:
        async_to_sync(channel_layer.group_send)(
            'kitchen_orders',
            {
                'type': 'new_order',
                'order_id': active_order.pk,
                'order_number': active_order.order_number,
                'table_number': f"P-{table.number}" if table.is_parcel else f"{table.number}",
                'waiter': waiter.name,
            }
        )
    except Exception:
        pass
    
    if items_added > 0:
        messages.success(request, f'Order placed! {items_added} item(s) sent to kitchen.')
    else:
        messages.warning(request, 'No items were selected.')
    
    return redirect('waiter:order_detail', order_pk=active_order.pk)


@waiter_required
def order_detail(request, order_pk):
    order = get_object_or_404(Order, pk=order_pk)
    return render(request, 'waiter/order_detail.html', {
        'order': order,
        'waiter_name': request.session.get('waiter_name'),
        'settings': get_settings(),
    })


@waiter_required
def generate_bill(request, order_pk):
    order = get_object_or_404(Order, pk=order_pk)
    settings_obj = get_settings()
    
    # Check if bill already exists
    try:
        bill = order.bill
    except Bill.DoesNotExist:
        subtotal = order.total_amount
        bill = Bill.objects.create(
            order=order,
            subtotal=subtotal,
            tax_percent=settings_obj.tax_percent,
            discount_percent=float(request.POST.get('discount', 0)) if request.method == 'POST' else 0,
            total=subtotal,  # Will be recalculated in save()
            payment_method=request.POST.get('payment_method', 'cash') if request.method == 'POST' else 'cash',
        )
        order.status = 'billed'
        order.save()
    
    return render(request, 'waiter/bill.html', {
        'bill': bill,
        'order': order,
        'waiter_name': request.session.get('waiter_name'),
        'settings': settings_obj,
    })


@waiter_required
def print_bill(request, bill_pk):
    bill = get_object_or_404(Bill, pk=bill_pk)
    settings_obj = get_settings()
    from core.printer import print_bill as do_print, generate_receipt_text
    success, message = do_print(bill, settings_obj)
    receipt_text = generate_receipt_text(bill, settings_obj)
    
    return render(request, 'waiter/print_result.html', {
        'bill': bill,
        'success': success,
        'message': message,
        'receipt_text': receipt_text,
        'waiter_name': request.session.get('waiter_name'),
        'settings': settings_obj,
    })


@waiter_required
def mark_paid(request, bill_pk):
    if request.method == 'POST':
        bill = get_object_or_404(Bill, pk=bill_pk)
        bill.is_paid = True
        bill.paid_at = timezone.now()
        bill.payment_method = request.POST.get('payment_method', 'cash')
        
        # Apply discount if provided
        discount = float(request.POST.get('discount_percent', 0))
        if discount != float(bill.discount_percent):
            bill.discount_percent = discount
        
        bill.save()
        
        # Free the table
        bill.order.table.status = 'free'
        bill.order.table.save()
        bill.order.status = 'billed'
        bill.order.save()
        
        messages.success(request, f'Payment of ₹{bill.total} received! Table freed.')
        return redirect('waiter:tables')
    return redirect('waiter:generate_bill', order_pk=bill.order.pk)


@waiter_required
def cancel_order(request, order_pk):
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=order_pk)
        order.status = 'cancelled'
        order.save()
        order.table.status = 'free'
        order.table.save()
        messages.info(request, 'Order cancelled.')
    return redirect('waiter:tables')


@waiter_required
def pay_quick(request, bill_pk):
    """Quick payment page accessible directly from the table modal."""
    bill = get_object_or_404(Bill, pk=bill_pk)
    settings_obj = get_settings()

    if request.method == 'POST':
        bill.is_paid = True
        bill.paid_at = timezone.now()
        bill.payment_method = request.POST.get('payment_method', 'cash')
        discount = float(request.POST.get('discount_percent', 0))
        if discount != float(bill.discount_percent):
            bill.discount_percent = discount
        bill.save()
        # Free the table
        bill.order.table.status = 'free'
        bill.order.table.save()
        bill.order.status = 'billed'
        bill.order.save()
        messages.success(request, f'Payment of ₹{bill.total} received via {bill.get_payment_method_display()}! Table freed.')
        return redirect('waiter:tables')

    return render(request, 'waiter/pay_quick.html', {
        'bill': bill,
        'waiter_name': request.session.get('waiter_name'),
        'settings': settings_obj,
    })


@waiter_required
def mark_order_served(request, order_pk):
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=order_pk)
        order.status = 'served'
        order.items.all().update(status='served')
        order.save()
        
        # Broadcast to TV display and kitchen via WebSocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        try:
            async_to_sync(channel_layer.group_send)(
                'tv_display',
                {
                    'type': 'order_update',
                    'order_id': order.pk,
                    'order_number': order.order_number,
                    'table_number': f"P-{order.table.number}" if order.table.is_parcel else f"{order.table.number}",
                    'status': 'served',
                }
            )
        except Exception:
            pass
            
        try:
            async_to_sync(channel_layer.group_send)(
                'kitchen_orders',
                {
                    'type': 'order_update',
                    'order_id': order.pk,
                    'order_number': order.order_number,
                    'status': 'served',
                }
            )
        except Exception:
            pass

        messages.success(request, f'Order #{order.order_number} marked as served.')
    return redirect('waiter:order_detail', order_pk=order_pk)

