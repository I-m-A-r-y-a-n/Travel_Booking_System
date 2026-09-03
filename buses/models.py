from django.db import models


class Bus(models.Model):
    operator_name = models.CharField(max_length=100)
    bus_number = models.CharField(max_length=20, unique=True)
    starting_location = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    total_seats = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.operator_name} ({self.bus_number}): {self.starting_location} → {self.destination}"