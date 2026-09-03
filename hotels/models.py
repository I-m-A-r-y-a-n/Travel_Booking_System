from django.db import models

class Hotel(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0.0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.location}"


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
        return f"{self.hotel.name} - {self.room_type} ({self.available_rooms} available)"