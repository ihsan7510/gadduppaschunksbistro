"""URL configuration for restaurant project."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', lambda request: redirect('admin_panel:dashboard'), name='home'),
    path('admin-panel/', include('admin_panel.urls', namespace='admin_panel')),
    path('waiter/', include('waiter.urls', namespace='waiter')),
    path('kitchen/', include('kitchen.urls', namespace='kitchen')),
    path('tv/', include('tv_display.urls', namespace='tv_display')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
