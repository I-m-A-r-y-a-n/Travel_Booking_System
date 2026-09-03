from django.db import models

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

    # NOTE: booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE)
    # This will be added once the Booking model exists in bookings/models.py.
    # For now, Payment exists as a standalone foundation.

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.status} - {self.amount}"