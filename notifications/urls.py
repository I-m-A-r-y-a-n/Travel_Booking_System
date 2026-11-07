from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('panel/', views.notification_panel, name='panel'),
    path('open/<int:notification_id>/', views.open_notification, name='open'),
    path('read/<int:notification_id>/', views.mark_read, name='mark_read'),
    path('read-all/', views.mark_all_read, name='mark_all_read'),
]