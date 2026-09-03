from django.urls import path
from . import views

urlpatterns = [
    path('book/flight/<int:flight_id>/', views.book_flight_view, name='book_flight'),
    path('book/bus/<int:bus_id>/', views.book_bus_view, name='book_bus'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
]