from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.bus_search_view, name='bus_search'),
    path('<int:bus_id>/', views.bus_detail_view, name='bus_detail'),
]