from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from flights.models import Flight
from buses.models import Bus
from travelbooking.helpers import parse_int
from .models import Booking
from .ticket_pdf import build_ticket_pdf
from .tickets import paid_payment, ticket_info
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
    bookings = list(
        Booking.objects.filter(user=request.user)
        .select_related('flight', 'bus', 'hotel', 'room', 'review')
        .order_by('-booking_date')
    )
    for booking in bookings:
        booking.info = ticket_info(booking)
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


def _timeline(booking, payments):
    """Booked -> Payment -> Confirmed/Cancelled, as [{label, note, state}]."""
    paid = next((p for p in payments if p.status == 'SUCCESS'), None)
    failed = next((p for p in payments if p.status == 'FAILED'), None)
    steps = [{'label': 'Booking placed', 'note': booking.booking_date, 'state': 'done'}]
    if paid:
        steps.append({'label': 'Payment received', 'note': paid.created_at, 'state': 'done'})
    elif failed:
        steps.append({'label': 'Payment failed', 'note': failed.created_at, 'state': 'fail'})
    elif booking.status == 'cancelled':
        steps.append({'label': 'No payment made', 'note': None, 'state': 'fail'})
    else:
        steps.append({'label': 'Awaiting payment', 'note': None, 'state': 'active'})
    if booking.status == 'confirmed':
        steps.append({'label': 'Booking confirmed', 'note': None, 'state': 'done'})
    elif booking.status == 'cancelled':
        steps.append({'label': 'Booking cancelled', 'note': None, 'state': 'fail'})
    else:
        steps.append({'label': 'Confirmation', 'note': None, 'state': ''})
    return steps


@login_required
def booking_detail_view(request, booking_id):
    """Everything about one booking: trip, facilities, payment, actions."""
    booking = get_object_or_404(
        Booking.objects.select_related('flight', 'bus', 'hotel', 'room', 'review'),
        id=booking_id, user=request.user,
    )
    payments = list(booking.payment_set.order_by('-created_at'))
    kind = booking.booking_type
    item = booking.flight if kind == 'flight' else booking.bus if kind == 'bus' else booking.hotel
    review = getattr(booking, 'review', None)
    if review is not None:
        review.star_list = [n < review.rating for n in range(5)]
    return render(request, 'bookings/booking_detail.html', {
        'booking': booking,
        'info': ticket_info(booking),
        'kind': kind,
        'item': item,
        'payments': payments,
        'paid': paid_payment(booking),
        'timeline': _timeline(booking, payments),
        'review': review,
    })


@login_required
def download_ticket_view(request, booking_id):
    """PDF ticket for one of the user's confirmed bookings."""
    booking = get_object_or_404(
        Booking.objects.select_related('flight', 'bus', 'hotel', 'room'),
        id=booking_id, user=request.user,
    )
    if booking.status != 'confirmed':
        messages.error(request, 'Tickets are only available for confirmed bookings.')
        return redirect('my_bookings')

    info = ticket_info(booking)
    pdf = build_ticket_pdf(info, request.user, paid_payment(booking))
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Wayfare-ticket-{info["ref"]}.pdf"'
    return response


@login_required
def cancel_booking_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        return redirect('my_bookings')

    return render(request, 'bookings/cancel_booking.html', {'booking': booking})
