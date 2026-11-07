from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.flight_search_view, name='flight_search'),
    path('<int:flight_id>/', views.flight_detail_view, name='flight_detail'),
]