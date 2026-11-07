from django.db import models

from travelbooking.helpers import format_duration, initials, parse_amenities

DEFAULT_FLIGHT_AMENITIES = (
    'Cabin baggage 7 kg, Check-in baggage 15 kg, In-flight meals available, Web check-in'
)


class Flight(models.Model):
    airline_name = models.CharField(max_length=100)
    flight_number = models.CharField(max_length=20, unique=True)
    departure_city = models.CharField(max_length=100)
    destination_city = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    total_seats = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amenities = models.TextField(
        blank=True,
        default=DEFAULT_FLIGHT_AMENITIES,
        help_text='Comma-separated list shown on the flight page, e.g. "Cabin baggage 7 kg, In-flight meals".',
    )

    def __str__(self):
        return f"{self.airline_name} ({self.flight_number}): {self.departure_city} → {self.destination_city}"

    # Shared names so flights and buses can use the same templates.
    @property
    def carrier(self):
        return self.airline_name

    @property
    def number(self):
        return self.flight_number

    @property
    def origin(self):
        return self.departure_city

    @property
    def dest(self):
        return self.destination_city

    @property
    def tag(self):
        return 'Non-stop'

    @property
    def logo_text(self):
        return initials(self.airline_name)

    @property
    def duration(self):
        return format_duration(self.departure_time, self.arrival_time)

    @property
    def duration_minutes(self):
        return int((self.arrival_time - self.departure_time).total_seconds() // 60)

    @property
    def day_offset(self):
        return max(0, (self.arrival_time.date() - self.departure_time.date()).days)

    @property
    def amenity_items(self):
        return parse_amenities(self.amenities)