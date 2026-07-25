from django.urls import path
from . import views

app_name = 'tv_display'

urlpatterns = [
    path('', views.tv_display, name='display'),
]
