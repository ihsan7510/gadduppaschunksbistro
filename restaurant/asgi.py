"""
ASGI config for restaurant project - supports WebSockets via Django Channels.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import kitchen.routing
import tv_display.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            kitchen.routing.websocket_urlpatterns +
            tv_display.routing.websocket_urlpatterns
        )
    ),
})
