from django.db.models import Sum

from .models import Booking
from .rules import holding_q


def seats_available(item, field):
    """Seats still free on a flight/bus. `field` is 'flight' or 'bus'.

    Confirmed bookings and unpaid bookings that are still inside their hold window
    (see bookings.rules.HOLD_MINUTES) take up seats; cancelled and lapsed ones do not.
    """
    booked = (
        Booking.objects.filter(holding_q(), **{field: item})
        .aggregate(total=Sum('passengers'))['total']
        or 0
    )
    return max(item.total_seats - booked, 0)
