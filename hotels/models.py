from django.db import models

from travelbooking.helpers import parse_amenities

DEFAULT_HOTEL_AMENITIES = 'Free WiFi, Air conditioning, 24x7 front desk, Room service, Parking'


class Hotel(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0.0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image_url = models.URLField(
        max_length=500,
        blank=True,
        help_text='Optional photo of the hotel (a full https:// link). A default photo is used when empty.',
    )
    amenities = models.TextField(
        blank=True,
        default=DEFAULT_HOTEL_AMENITIES,
        help_text='Comma-separated list shown on the hotel page, e.g. "Free WiFi, Swimming pool, Parking".',
    )

    def __str__(self):
        return f"{self.name} - {self.location}"

    @property
    def amenity_items(self):
        return parse_amenities(self.amenities)

    @property
    def placeholder_variant(self):
        """0-3: picks which crop of the default photo to show, so hotels without a
        photo of their own don't all look identical."""
        return (self.pk or 0) % 4


class Room(models.Model):
    ROOM_TYPE_CHOICES = [
        ('STANDARD', 'Standard'),
        ('DELUXE', 'Deluxe'),
        ('SUITE', 'Suite'),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.PositiveIntegerField(help_text="Max guests this room can hold")
    total_rooms = models.PositiveIntegerField()
    available_rooms = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.hotel.name} - {self.room_type} (capacity: {self.total_rooms})"