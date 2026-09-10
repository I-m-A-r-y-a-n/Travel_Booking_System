from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.bus_search_view, name='bus_search'),
]