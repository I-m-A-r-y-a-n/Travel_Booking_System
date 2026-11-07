from django.db.models import Sum

from .models import Booking

HOLDING_STATUSES = ['pending', 'confirmed']


def seats_available(item, field):
    """Seats still free on a flight/bus. `field` is 'flight' or 'bus'.
    Pending bookings hold their seats, same as before."""
    booked = (
        Booking.objects.filter(**{field: item}, status__in=HOLDING_STATUSES)
        .aggregate(total=Sum('passengers'))['total']
        or 0
    )
    return max(item.total_seats - booked, 0)