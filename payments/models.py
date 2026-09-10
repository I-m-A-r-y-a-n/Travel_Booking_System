from django.db import models
from bookings.models import Booking
class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('CARD', 'Card'),
        ('UPI', 'UPI'),
        ('NETBANKING', 'Net Banking'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.status} - {self.amount}"