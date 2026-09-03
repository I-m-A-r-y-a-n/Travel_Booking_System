from django.db import models


class Flight(models.Model):
    airline_name = models.CharField(max_length=100)
    flight_number = models.CharField(max_length=20, unique=True)
    departure_city = models.CharField(max_length=100)
    destination_city = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    total_seats = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.airline_name} ({self.flight_number}): {self.departure_city} → {self.destination_city}"