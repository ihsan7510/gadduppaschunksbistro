from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from core.models import (
    RestaurantTable, Category, MenuItem, Order, OrderItem, RestaurantSettings
)

def get_settings():
    obj, _ = RestaurantSettings.objects.get_or_create(pk=1)
    return obj

def table_order(request, table_number):
    table = get_object_or_404(RestaurantTable, number=table_number)
    
    # Store table number in session
    request.session['customer_table'] = table.number
    
    categories = Category.objects.prefetch_related('items').filter(items__is_available=True).distinct()
    
    # Check for existing active order for this table
    active_order = table.orders.filter(
        status__in=['pending', 'confirmed', 'preparing', 'ready', 'served']
    ).first()
    
    context = {
        'table': table,
        'categories': categories,
        'active_order': active_order,
        'settings': get_settings(),
    }
    return render(request, 'customer/table_order.html', context)

def place_order(request):
    if request.method != 'POST':
        return redirect('home')
        
    table_number = request.session.get('customer_table')
    if not table_number:
        messages.error(request, 'Session expired or table not identified. Please scan the QR code again.')
        return redirect('home')
        
    table = get_object_or_404(RestaurantTable, number=table_number)
    
    # Check for existing active order (if table is occupied/ordering more)
    active_order = table.orders.filter(
        status__in=['pending', 'confirmed', 'preparing']
    ).first()
    
    is_new_order = False
    if not active_order:
        active_order = Order.objects.create(
            table=table,
            waiter=None, # Customer self order has no waiter
            status='confirmed', # Sent directly to kitchen
            notes=request.POST.get('order_notes', ''),
        )
        table.status = 'occupied'
        table.save()
        is_new_order = True
        
    items_added = 0
    for key, value in request.POST.items():
        if key.startswith('qty_'):
            menu_item_id = key.replace('qty_', '')
            try:
                qty = int(value)
                if qty > 0:
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
            except (ValueError, MenuItem.DoesNotExist):
                pass
                
    if items_added > 0:
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
                    'table_number': table.number,
                    'waiter': 'Customer (Self)',
                }
            )
        except Exception:
            pass
        messages.success(request, 'Your order has been successfully placed!')
    else:
        # If we created a blank order with no items, delete it
        if is_new_order:
            active_order.delete()
            table.status = 'free'
            table.save()
        messages.warning(request, 'No items were selected.')
        return redirect('customer:table_order', table_number=table.number)
        
    return redirect('customer:order_status')

def order_status(request):
    table_number = request.session.get('customer_table')
    if not table_number:
        messages.error(request, 'Please scan a table QR code to view order status.')
        return redirect('home')
        
    table = get_object_or_404(RestaurantTable, number=table_number)
    
    # Get active orders (including served and billed ones for this session)
    active_orders = table.orders.filter(
        status__in=['pending', 'confirmed', 'preparing', 'ready', 'served', 'billed']
    ).prefetch_related('items__menu_item').order_by('-created_at')
    
    context = {
        'table': table,
        'active_orders': active_orders,
        'settings': get_settings(),
    }
    return render(request, 'customer/order_status.html', context)
