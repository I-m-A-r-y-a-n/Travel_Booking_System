from django.urls import path
from . import views

urlpatterns = [
    path('book/flight/<int:flight_id>/', views.book_flight_view, name='book_flight'),
    path('book/bus/<int:bus_id>/', views.book_bus_view, name='book_bus'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('<int:booking_id>/', views.booking_detail_view, name='booking_detail'),
    path('cancel/<int:booking_id>/', views.cancel_booking_view, name='cancel_booking'),
    path('ticket/<int:booking_id>/', views.download_ticket_view, name='download_ticket'),
]
