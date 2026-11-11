from datetime import date
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from bookings.models import Booking
from bookings.rules import expire_stale, holding_q, stay_error
from reviews.utils import review_summary
from travelbooking.helpers import parse_date, parse_int

from .models import Hotel, Room


def _stay_error(check_in, check_out):
    """Message for an unusable date pair, or None when it is fine."""
    return stay_error(check_in, check_out)


def _rooms_left(room, check_in, check_out):
    """How many rooms of this type are still free for the given dates.
    Confirmed bookings and unpaid ones still on hold take a room."""
    overlapping = Booking.objects.filter(
        holding_q(),
        room=room,
        check_in_date__lt=check_out,
        check_out_date__gt=check_in,
    ).count()
    return max(room.total_rooms - overlapping, 0)


def _stay_query(check_in, check_out, guests):
    """'check_in=...&check_out=...&guests=...' built only from validated values."""
    params = {}
    if check_in:
        params['check_in'] = check_in.isoformat()
    if check_out:
        params['check_out'] = check_out.isoformat()
    if guests:
        params['guests'] = guests
    return urlencode(params)


def search_hotels(request):
    destination = request.GET.get('destination', '').strip()
    check_in_date = parse_date(request.GET.get('check_in'))
    check_out_date = parse_date(request.GET.get('check_out'))
    guests = parse_int(request.GET.get('guests'), minimum=1)
    sort = request.GET.get('sort', '')

    has_dates = bool(check_in_date and check_out_date)
    error = _stay_error(check_in_date, check_out_date) if has_dates else None
    nights = (check_out_date - check_in_date).days if has_dates and not error else None

    hotels = []
    searched = bool(request.GET)
    if searched and not error:  # a first visit shows the "Find your stay" prompt, not every hotel
        rooms = Room.objects.select_related('hotel').order_by('price_per_night')
        if destination:
            rooms = rooms.filter(hotel__location__icontains=destination)
        if guests:
            rooms = rooms.filter(capacity__gte=guests)

        grouped = {}
        for room in rooms:
            if has_dates and _rooms_left(room, check_in_date, check_out_date) <= 0:
                continue
            entry = grouped.setdefault(room.hotel_id, {'hotel': room.hotel, 'rooms': []})
            entry['rooms'].append(room)

        for entry in grouped.values():
            entry['room_count'] = len(entry['rooms'])
            entry['min_price'] = entry['rooms'][0].price_per_night  # rooms are ordered by price
            entry['max_capacity'] = max(r.capacity for r in entry['rooms'])
            if nights:
                entry['stay_total'] = entry['min_price'] * nights
            hotels.append(entry)

        if sort == 'price':
            hotels.sort(key=lambda h: h['min_price'])
        elif sort == 'rating':
            hotels.sort(key=lambda h: h['hotel'].rating, reverse=True)
        else:
            hotels.sort(key=lambda h: (-h['hotel'].rating, h['min_price']))

    context = {
        'hotels': hotels,
        'searched': searched,
        'error': error,
        'destination': destination,
        'guests': guests or '',
        'check_in': check_in_date.isoformat() if check_in_date else '',
        'check_out': check_out_date.isoformat() if check_out_date else '',
        'nights': nights,
        'sort': sort,
        'stay_query': _stay_query(check_in_date, check_out_date, guests),
        'locations': sorted(Hotel.objects.values_list('location', flat=True).distinct()),
        'today': date.today(),
    }
    return render(request, 'hotels/search_results.html', context)


def hotel_detail(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    check_in_date = parse_date(request.GET.get('check_in'))
    check_out_date = parse_date(request.GET.get('check_out'))
    guests = parse_int(request.GET.get('guests'), minimum=1)

    has_dates = bool(check_in_date and check_out_date)
    error = _stay_error(check_in_date, check_out_date) if has_dates else None
    nights = (check_out_date - check_in_date).days if has_dates and not error else None

    rooms = list(hotel.rooms.order_by('price_per_night'))
    for room in rooms:
        room.fits_guests = guests is None or room.capacity >= guests
        room.left = _rooms_left(room, check_in_date, check_out_date) if nights else None
        room.stay_total = room.price_per_night * nights if nights else None
        room.can_book = bool(nights) and room.fits_guests and room.left > 0
        room.book_query = _stay_query(check_in_date, check_out_date, guests)

    context = {
        'hotel': hotel,
        'rooms': rooms,
        'check_in': check_in_date.isoformat() if check_in_date else '',
        'check_out': check_out_date.isoformat() if check_out_date else '',
        'check_in_date': check_in_date,
        'check_out_date': check_out_date,
        'guests': guests or '',
        'nights': nights,
        'error': error,
        'today': date.today(),
        'reviews': review_summary('hotel', hotel),
        'stay_query': _stay_query(check_in_date, check_out_date, guests),
    }
    return render(request, 'hotels/hotel_detail.html', context)


@login_required
def book_room(request, room_id):
    """GET shows the review page; POST creates the pending booking."""
    expire_stale(request.user)
    room = get_object_or_404(Room.objects.select_related('hotel'), id=room_id)
    source = request.POST if request.method == 'POST' else request.GET

    check_in_date = parse_date(source.get('check_in'))
    check_out_date = parse_date(source.get('check_out'))
    guests = parse_int(source.get('guests'), default=1, minimum=1)

    def failed(reason):
        return render(request, 'hotels/booking_failed.html', {
            'room': room,
            'hotel': room.hotel,
            'reason': reason,
            'stay_query': _stay_query(check_in_date, check_out_date, guests),
        })

    if not check_in_date or not check_out_date:
        return failed('Please select check-in and check-out dates before booking.')

    error = _stay_error(check_in_date, check_out_date)
    if error:
        return failed(error)

    if guests > room.capacity:
        return failed(f'This room holds up to {room.capacity} guest(s). Please choose a larger room.')

    rooms_left = _rooms_left(room, check_in_date, check_out_date)
    if rooms_left <= 0:
        return failed('No rooms available for the selected dates.')

    nights = (check_out_date - check_in_date).days
    total_price = room.price_per_night * nights

    if request.method == 'POST':
        with transaction.atomic():
            # Lock the room row so two people can't take the last room at the same moment.
            locked = Room.objects.select_for_update().get(pk=room.pk)
            existing = (
                Booking.objects.filter(
                    holding_q(), user=request.user, status='pending', room=locked,
                    check_in_date=check_in_date, check_out_date=check_out_date,
                ).first()
            )
            if existing is None and _rooms_left(locked, check_in_date, check_out_date) <= 0:
                return failed('No rooms available for the selected dates.')
            if existing:  # same user clicked again: reuse their booking instead of holding twice
                existing.passengers = guests
                existing.total_price = total_price
                existing.save(update_fields=['passengers', 'total_price'])
                booking = existing
            else:
                booking = Booking.objects.create(
                    user=request.user,
                    booking_type='hotel',
                    hotel=room.hotel,
                    room=room,
                    check_in_date=check_in_date,
                    check_out_date=check_out_date,
                    passengers=guests,
                    total_price=total_price,
                    status='pending',
                )
        return redirect('payments:choose_payment_method', booking_id=booking.id)

    return render(request, 'hotels/confirm_booking.html', {
        'room': room,
        'hotel': room.hotel,
        'check_in': check_in_date,
        'check_out': check_out_date,
        'nights': nights,
        'guests': guests,
        'total_price': total_price,
        'rooms_left': rooms_left,
        'stay_query': _stay_query(check_in_date, check_out_date, guests),
    })
