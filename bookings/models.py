from django.db import models
from django.conf import settings
from flights.models import Flight
from buses.models import Bus


class Booking(models.Model):
    BOOKING_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('bus', 'Bus'),
        ('hotel', 'Hotel'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    booking_type = models.CharField(max_length=10, choices=BOOKING_TYPE_CHOICES)

    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, null=True, blank=True)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, null=True, blank=True)
    # hotel field will be added by Harish once the Hotel model exists

    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Booking #{self.id} - {self.user} - {self.booking_type}"
