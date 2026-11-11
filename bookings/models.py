from django.db import models
from django.conf import settings
from flights.models import Flight
from buses.models import Bus
from hotels.models import Hotel
from hotels.models import Room

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
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    check_in_date = models.DateField(null=True, blank=True)
    check_out_date = models.DateField(null=True, blank=True)

    passengers = models.PositiveIntegerField(default=1)
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Round trips: the outbound and return bookings share a group_ref and are paid together.
    group_ref = models.CharField(max_length=32, blank=True, db_index=True)
    leg = models.CharField(max_length=10, blank=True, choices=[('outbound', 'Outbound'), ('return', 'Return')])

    def __str__(self):
        return f"Booking #{self.id} - {self.user} - {self.booking_type}"


class Passenger(models.Model):
    """One traveller on a flight or bus booking (name, age, gender and the seat they chose)."""
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='travellers')
    name = models.CharField(max_length=100)
    age = models.PositiveSmallIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    seat = models.CharField(max_length=8, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.name} ({self.age}) on booking #{self.booking_id}"
