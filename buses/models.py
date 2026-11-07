from django.db import models

from travelbooking.helpers import format_duration, initials, parse_amenities

DEFAULT_BUS_AMENITIES = (
    'Air conditioning, Charging point, Reading light, Water bottle, Live bus tracking'
)


class Bus(models.Model):
    BUS_TYPE_CHOICES = [
        ('AC_SEATER', 'AC Seater'),
        ('NONAC_SEATER', 'Non-AC Seater'),
        ('AC_SLEEPER', 'AC Sleeper'),
        ('NONAC_SLEEPER', 'Non-AC Sleeper'),
        ('VOLVO', 'Volvo Multi-Axle'),
    ]

    operator_name = models.CharField(max_length=100)
    bus_number = models.CharField(max_length=20, unique=True)
    starting_location = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    total_seats = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    bus_type = models.CharField(max_length=20, choices=BUS_TYPE_CHOICES, default='AC_SEATER')
    amenities = models.TextField(
        blank=True,
        default=DEFAULT_BUS_AMENITIES,
        help_text='Comma-separated list shown on the bus page, e.g. "Air conditioning, Charging point".',
    )
    image_url = models.URLField(
        max_length=500,
        blank=True,
        help_text='Optional photo of the bus (a full https:// link).',
    )

    def __str__(self):
        return f"{self.operator_name} ({self.bus_number}): {self.starting_location} → {self.destination}"

    # Shared names so flights and buses can use the same templates.
    @property
    def carrier(self):
        return self.operator_name

    @property
    def number(self):
        return self.bus_number

    @property
    def origin(self):
        return self.starting_location

    @property
    def dest(self):
        return self.destination

    @property
    def tag(self):
        return self.get_bus_type_display()

    @property
    def logo_text(self):
        return initials(self.operator_name)

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
