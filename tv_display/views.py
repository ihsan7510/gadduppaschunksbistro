"""TV Display Module Views"""

from django.shortcuts import render
from core.models import Order, RestaurantSettings


def get_settings():
    obj, _ = RestaurantSettings.objects.get_or_create(pk=1)
    return obj


def tv_display(request):
    """Main TV display - shows live order status for customers."""
    active_orders = Order.objects.filter(
        status__in=['confirmed', 'preparing', 'ready', 'served']
    ).prefetch_related('items__menu_item').select_related('table').order_by('-created_at')[:20]
    
    preparing = [o for o in active_orders if o.status in ['confirmed', 'preparing']]
    ready = [o for o in active_orders if o.status == 'ready']
    
    context = {
        'preparing': preparing,
        'ready': ready,
        'settings': get_settings(),
    }
    return render(request, 'tv_display/display.html', context)
