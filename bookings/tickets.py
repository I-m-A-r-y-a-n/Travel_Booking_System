"""Turns a Booking into plain ticket data, shared by the web pages and the PDF."""
from django.utils import timezone

from travelbooking.helpers import initials

ICONS = {'flight': 'plane', 'bus': 'bus', 'hotel': 'building'}
UNITS = {'flight': 'passenger', 'bus': 'seat', 'hotel': 'guest'}


def booking_ref(booking):
    """Human friendly reference, e.g. WF000123."""
    return f'WF{booking.pk:06d}'


def _local(value):
    if value is not None and timezone.is_aware(value):
        return timezone.localtime(value)
    return value


def _plural(count, word):
    return f'{count} {word}{"" if count == 1 else "s"}'


def ticket_info(booking):
    """Everything a ticket needs, as one dict. Missing related objects give blanks."""
    kind = booking.booking_type
    info = {
        'id': booking.pk,
        'ref': booking_ref(booking),
        'kind': kind,
        'kind_label': booking.get_booking_type_display(),
        'icon': ICONS.get(kind, 'check'),
        'unit': UNITS.get(kind, 'passenger'),
        'status': booking.status,
        'status_label': booking.get_status_display(),
        'passengers': booking.passengers,
        'total': booking.total_price,
        'booked_on': _local(booking.booking_date),
        'title': '', 'number': '', 'tag': '', 'logo_text': '?',
        'origin': '', 'dest': '', 'depart': None, 'arrive': None, 'duration': '', 'day_offset': 0,
        'check_in': None, 'check_out': None, 'nights': None,
        'unit_price': None, 'qty': 1, 'qty_text': '', 'start_date': None, 'summary': '',
        'leg': booking.leg, 'leg_label': booking.get_leg_display() if booking.leg else '',
        'travellers': [], 'seats': '',
    }
    if kind in ('flight', 'bus'):
        info['travellers'] = [
            {'name': p.name, 'age': p.age, 'gender': p.get_gender_display(), 'seat': p.seat}
            for p in booking.travellers.all()
        ]
        info['seats'] = ', '.join(p['seat'] for p in info['travellers'] if p['seat'])

    trip = booking.flight if kind == 'flight' else booking.bus if kind == 'bus' else None
    if trip is not None:
        info.update(
            title=trip.carrier, number=trip.number, tag=trip.tag, logo_text=trip.logo_text,
            origin=trip.origin, dest=trip.dest,
            depart=_local(trip.departure_time), arrive=_local(trip.arrival_time),
            duration=trip.duration, day_offset=trip.day_offset,
            unit_price=trip.price, qty=booking.passengers,
            qty_text=_plural(booking.passengers, info['unit']),
        )
        info['start_date'] = info['depart'].date()
        info['summary'] = f'{trip.origin} to {trip.dest}'

    elif kind == 'hotel' and booking.hotel is not None:
        hotel, room = booking.hotel, booking.room
        nights = None
        if booking.check_in_date and booking.check_out_date:
            nights = (booking.check_out_date - booking.check_in_date).days
        info.update(
            title=hotel.name, logo_text=initials(hotel.name), origin=hotel.location,
            number=f'{room.get_room_type_display()} room' if room else '',
            tag=_plural(nights, 'night') if nights else '',
            check_in=booking.check_in_date, check_out=booking.check_out_date, nights=nights,
            unit_price=room.price_per_night if room else None,
            qty=nights or 1, qty_text=_plural(nights, 'night') if nights else '',
            start_date=booking.check_in_date,
        )
        info['summary'] = f'{hotel.name}, {hotel.location}'

    return info


def paid_payment(booking):
    """The successful payment for a booking, or None."""
    return booking.payment_set.filter(status='SUCCESS').order_by('-created_at').first()
