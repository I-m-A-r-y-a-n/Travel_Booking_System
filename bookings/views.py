from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from flights.models import Flight
from buses.models import Bus
from travelbooking.helpers import parse_int
from .models import Booking
from .utils import seats_available


def _book_trip(request, item, kind):
    """Shared flow for flights and buses (`kind` is 'flight' or 'bus').

    GET  -> review page with the trip details and fare summary.
    POST -> create the pending booking and go to payment.
    """
    seats_left = seats_available(item, kind)
    source = request.POST if request.method == 'POST' else request.GET
    passengers = parse_int(source.get('passengers'), default=1, minimum=1)

    if request.method == 'POST' and passengers <= seats_left:
        booking = Booking.objects.create(
            user=request.user,
            booking_type=kind,
            passengers=passengers,
            total_price=item.price * passengers,
            status='pending',
            **{kind: item},
        )
        return redirect('payments:choose_payment_method', booking_id=booking.id)

    return render(request, 'bookings/confirm_booking.html', {
        'item': item,
        'kind': kind,
        'item_type': kind.capitalize(),
        'unit': 'passenger' if kind == 'flight' else 'seat',
        'detail_url': f'{kind}_detail',
        'seats_available': seats_left,
        'passengers': passengers,
        'total_price': item.price * passengers,
        'sold_out': passengers > seats_left,
    })


@login_required
def book_flight_view(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    return _book_trip(request, flight, 'flight')


@login_required
def book_bus_view(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id)
    return _book_trip(request, bus, 'bus')


@login_required
def my_bookings_view(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


@login_required
def cancel_booking_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        return redirect('my_bookings')

    return render(request, 'bookings/cancel_booking.html', {'booking': booking})
