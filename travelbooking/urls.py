from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('hotels/', include('hotels.urls')),
    path('flights/', include('flights.urls')),
    path('buses/', include('buses.urls')),
    path('bookings/', include('bookings.urls')),
]
