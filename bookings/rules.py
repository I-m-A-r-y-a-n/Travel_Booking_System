"""Booking rules in one place, so every view applies the same logic.

These follow the conventions of the big Indian booking sites (MakeMyTrip, ixigo, redBus):
unpaid bookings only hold seats for a short time, trips close for booking shortly before
departure, a booking has a passenger limit, and cancellations refund a share of the fare
that shrinks as the trip gets closer. Change the numbers below to tune any rule.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q
from django.utils import timezone

# ---- seat / room holds
HOLD_MINUTES = 15  # an unpaid booking keeps its seats for this long

# ---- limits
MAX_PER_BOOKING = {'flight': 9, 'bus': 6}   # passengers / seats in one booking
MAX_STAY_NIGHTS = 30
MAX_ADVANCE_DAYS = 365                      # how far ahead anything can be booked

# ---- booking closes this long before departure (check-in for hotels is date based)
BOOKING_CLOSES_BEFORE = {'flight': timedelta(hours=2), 'bus': timedelta(hours=1)}
HOTEL_CHECKIN_TIME = time(12, 0)            # used for hotel refund / completion maths
HOTEL_CHECKOUT_TIME = time(11, 0)

# ---- refunds: (hours before start, percent of the fare refunded), best tier first.
# Below the last tier the booking can no longer be cancelled.
REFUND_TIERS = {
    'flight': [(72, 90), (24, 75), (4, 50)],
    'bus': [(24, 90), (12, 75), (4, 50)],
    'hotel': [(48, 100), (24, 50), (0, 0)],
}
POLICY_LABELS = {
    'flight': ['More than 72 hours before departure: 90% refund', '24 to 72 hours: 75% refund',
               '4 to 24 hours: 50% refund', 'Less than 4 hours: cannot be cancelled'],
    'bus': ['More than 24 hours before departure: 90% refund', '12 to 24 hours: 75% refund',
            '4 to 12 hours: 50% refund', 'Less than 4 hours: cannot be cancelled'],
    'hotel': ['More than 48 hours before check-in: full refund', '24 to 48 hours: 50% refund',
              'Less than 24 hours: no refund'],
}


# --------------------------------------------------------------------------- holds
def hold_cutoff(now=None):
    return (now or timezone.now()) - timedelta(minutes=HOLD_MINUTES)


def holding_q(now=None):
    """Bookings that currently take up seats/rooms: confirmed, or pending and still on hold."""
    return Q(status='confirmed') | Q(status='pending', booking_date__gte=hold_cutoff(now))


def hold_expires_at(booking):
    return booking.booking_date + timedelta(minutes=HOLD_MINUTES)


def is_hold_expired(booking, now=None):
    return booking.status == 'pending' and hold_expires_at(booking) <= (now or timezone.now())


def expire_stale(user=None, now=None):
    """Cancel unpaid bookings whose hold ran out. Uses update(), so no 'cancelled'
    notification is sent for a hold that simply lapsed."""
    from .models import Booking
    qs = Booking.objects.filter(status='pending', booking_date__lt=hold_cutoff(now))
    if user is not None:
        qs = qs.filter(user=user)
    return qs.update(status='cancelled')


# --------------------------------------------------------------------------- start times
def _aware(value):
    return timezone.make_aware(value) if timezone.is_naive(value) else value


def start_datetime(booking):
    """When the trip or stay starts, as an aware datetime (None if unknown)."""
    if booking.booking_type == 'flight' and booking.flight:
        return booking.flight.departure_time
    if booking.booking_type == 'bus' and booking.bus:
        return booking.bus.departure_time
    if booking.booking_type == 'hotel' and booking.check_in_date:
        return _aware(datetime.combine(booking.check_in_date, HOTEL_CHECKIN_TIME))
    return None


def end_datetime(booking):
    """When the trip or stay is over."""
    if booking.booking_type == 'flight' and booking.flight:
        return booking.flight.arrival_time
    if booking.booking_type == 'bus' and booking.bus:
        return booking.bus.arrival_time
    if booking.booking_type == 'hotel' and booking.check_out_date:
        return _aware(datetime.combine(booking.check_out_date, HOTEL_CHECKOUT_TIME))
    return None


def trip_completed(booking, now=None):
    end = end_datetime(booking)
    return end is not None and end <= (now or timezone.now())


# --------------------------------------------------------------------------- can it be booked
def booking_closed_reason(item, kind, now=None):
    """Why a flight/bus can't be booked any more, or '' when it can."""
    now = now or timezone.now()
    departure = item.departure_time
    if departure <= now:
        return 'This departure has already left.'
    if departure - now < BOOKING_CLOSES_BEFORE[kind]:
        hours = int(BOOKING_CLOSES_BEFORE[kind].total_seconds() // 3600)
        return f'Booking closed. Tickets can be booked up to {hours} hour{"s" if hours != 1 else ""} before departure.'
    if departure.date() > timezone.localdate() + timedelta(days=MAX_ADVANCE_DAYS):
        return 'Bookings for this date are not open yet.'
    return ''


def max_per_booking(kind):
    return MAX_PER_BOOKING[kind]


def stay_error(check_in, check_out, today=None):
    """Message for an unusable hotel date pair, or None."""
    today = today or timezone.localdate()
    if check_out <= check_in:
        return 'Check-out date must be after check-in date.'
    if check_in < today:
        return 'Check-in date cannot be in the past.'
    if check_in > today + timedelta(days=MAX_ADVANCE_DAYS):
        return f'Hotels can be booked up to {MAX_ADVANCE_DAYS} days in advance.'
    if (check_out - check_in).days > MAX_STAY_NIGHTS:
        return f'You can book at most {MAX_STAY_NIGHTS} nights at a time.'
    return None


def search_date_error(value, today=None):
    """Message for a flight/bus search date that is in the past or too far ahead."""
    today = today or timezone.localdate()
    if value < today:
        return 'Please choose today or a future date.'
    if value > today + timedelta(days=MAX_ADVANCE_DAYS):
        return f'Please choose a date within the next {MAX_ADVANCE_DAYS} days.'
    return None


# --------------------------------------------------------------------------- cancellation
def _money(value):
    return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def refund_for(booking, now=None):
    """What cancelling this booking would do.

    Returns {'allowed': bool, 'percent': int, 'amount': Decimal, 'reason': str}.
    Unpaid (pending) bookings can always be cancelled and have nothing to refund.
    """
    now = now or timezone.now()
    if booking.status == 'cancelled':
        return {'allowed': False, 'percent': 0, 'amount': Decimal('0.00'), 'reason': 'This booking is already cancelled.'}
    start = start_datetime(booking)
    if booking.status == 'pending':
        return {'allowed': True, 'percent': 0, 'amount': Decimal('0.00'), 'reason': ''}
    if start is None:
        return {'allowed': True, 'percent': 0, 'amount': Decimal('0.00'), 'reason': ''}
    hours = (start - now).total_seconds() / 3600
    if hours <= 0:
        return {'allowed': False, 'percent': 0, 'amount': Decimal('0.00'),
                'reason': 'This trip has already started, so it can no longer be cancelled.'}
    for tier_hours, percent in REFUND_TIERS[booking.booking_type]:
        if hours >= tier_hours:
            if booking.booking_type == 'hotel' or percent > 0:
                return {'allowed': True, 'percent': percent,
                        'amount': _money(booking.total_price * percent / 100), 'reason': ''}
    return {'allowed': False, 'percent': 0, 'amount': Decimal('0.00'),
            'reason': 'Cancellation is closed because the trip starts in less than 4 hours.'}


# --------------------------------------------------------------------------- round trips
def group_of(booking, lock=False):
    """The bookings paid together with this one (a round trip's outbound + return), the
    outbound first. A normal booking is a group of one."""
    from .models import Booking
    if not booking.group_ref:
        return [booking]
    qs = Booking.objects.filter(user=booking.user, group_ref=booking.group_ref)
    if lock:
        qs = qs.select_for_update()
    return sorted(qs, key=lambda b: (b.leg != 'outbound', b.pk))
