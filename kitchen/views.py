"""Kitchen Module Views"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from core.models import Order, OrderItem, RestaurantSettings


def get_settings():
    obj, _ = RestaurantSettings.objects.get_or_create(pk=1)
    return obj


def kitchen_login(request):
    if request.session.get('kitchen_logged_in'):
        return redirect('kitchen:orders')
    error = None
    if request.method == 'POST':
        if request.POST.get('password') == 'kitchen123':
            request.session['kitchen_logged_in'] = True
            return redirect('kitchen:orders')
        error = 'Wrong password!'
    return render(request, 'kitchen/login.html', {'error': error, 'settings': get_settings()})


def kitchen_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('kitchen_logged_in'):
            return redirect('kitchen:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@kitchen_required
def orders(request):
    pending_orders = Order.objects.filter(
        status__in=['confirmed', 'preparing']
    ).prefetch_related('items__menu_item').select_related('table', 'waiter').order_by('created_at')
    
    context = {
        'pending_orders': pending_orders,
        'settings': get_settings(),
    }
    return render(request, 'kitchen/orders.html', context)


@kitchen_required
def update_item_status(request, item_pk):
    if request.method == 'POST':
        item = get_object_or_404(OrderItem, pk=item_pk)
        new_status = request.POST.get('status')
        if new_status in ['preparing', 'ready', 'served']:
            item.status = new_status
            item.save()
            
            # Update order status based on items
            order = item.order
            all_items = order.items.all()
            
            if all(i.status == 'ready' for i in all_items):
                order.status = 'ready'
            elif any(i.status in ['preparing', 'ready'] for i in all_items):
                order.status = 'preparing'
            order.save()
            
            # Broadcast to TV display and waiter via WebSocket
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
                        'table_number': order.table.number,
                        'status': order.status,
                    }
                )
            except Exception:
                pass
            
            return JsonResponse({'success': True, 'order_status': order.status})
    return JsonResponse({'success': False})


@kitchen_required
def complete_order(request, order_pk):
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=order_pk)
        order.items.filter(status='ready').update(status='served')
        order.status = 'served'
        order.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@kitchen_required
def order_history(request):
    today = timezone.now().date()
    completed = Order.objects.filter(
        status__in=['served', 'billed'],
        created_at__date=today
    ).prefetch_related('items__menu_item').select_related('table').order_by('-updated_at')
    
    return render(request, 'kitchen/history.html', {
        'completed': completed, 'settings': get_settings()
    })
