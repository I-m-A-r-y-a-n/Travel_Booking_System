from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "Travel Booking System Administration"
admin.site.site_title = "Travel Booking Admin"
admin.site.index_title = "Welcome to Travel Booking System Admin Panel"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('hotels/', include('hotels.urls')),
    path('payments/', include('payments.urls')),
    path('flights/', include('flights.urls')),
    path('buses/', include('buses.urls')),
    path('bookings/', include('bookings.urls')),
]
