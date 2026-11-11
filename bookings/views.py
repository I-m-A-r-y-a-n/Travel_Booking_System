import uuid

from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from flights.models import Flight
from buses.models import Bus
from travelbooking.helpers import parse_int
from .models import Booking, Passenger
from .passengers import GENDERS, blank_rows, read_passengers
from .rules import (
    booking_closed_reason, expire_stale, hold_cutoff, hold_expires_at,
    max_per_booking, POLICY_LABELS, refund_for, trip_completed,
)
from .ticket_pdf import build_ticket_pdf
from .tickets import paid_payment, ticket_info
from .seats import in_layout_order, seat_error, seat_layout, taken_seats
from .utils import seats_available


class Leg:
    """One trip being booked: the outbound, and for a round trip the return too."""

    def __init__(self, item, kind, role, index, user):
        self.item, self.kind, self.role, self.index = item, kind, role, index
        self.field = f'seats_{index}'
        self.fare = item.price
        self.closed = booking_closed_reason(item, kind)
        self.seats_left = seats_available(item, kind)
        # The user's own unpaid hold on this trip doesn't count as "taken" for them.
        own = (Booking.objects.filter(user=user, status='pending', booking_date__gte=hold_cutoff(),
                                      **{kind: item}).order_by('-booking_date').first())
        self.own_id = own.pk if own else None
        self.taken = taken_seats(item, kind, exclude_booking=self.own_id)
        self.chosen = []
        self.seat_problem = ''
        self.map = None


def _return_trip(item, kind, source):
    """(trip, error) for the optional ?return=<id> of a round trip."""
    raw = source.get('return')
    if not raw:
        return None, ''
    back = type(item).objects.filter(pk=parse_int(raw, default=0)).first()
    if back is None:
        return None, 'That return trip could not be found.'
    if back.origin.lower() != item.dest.lower() or back.dest.lower() != item.origin.lower():
        return None, 'The return trip must run the opposite way.'
    if back.departure_time <= item.arrival_time:
        return None, 'The return trip must leave after you arrive.'
    return back, ''


def _book_trip(request, item, kind):
    """Shared flow for flights and buses (`kind` is 'flight' or 'bus').

    GET  -> review page: trip summary, passenger details and seat selection.
    POST -> check the details, hold the seats and go to payment. For a round trip
            (?return=<id>) both legs are held together and paid in one go.
    """
    expire_stale(request.user)
    source = request.POST if request.method == 'POST' else request.GET
    limit = max_per_booking(kind)
    back, trip_error = _return_trip(item, kind, source)
    legs = [Leg(item, kind, 'Outbound' if back else '', 0, request.user)]
    if back:
        legs.append(Leg(back, kind, 'Return', 1, request.user))

    closed = next((leg.closed for leg in legs if leg.closed), '')
    seats_left = min(leg.seats_left for leg in legs)
    requested = parse_int(source.get('passengers'), default=1, minimum=1)
    passengers = min(requested, limit)
    unit = 'passenger' if kind == 'flight' else 'seat'
    error = trip_error or (f'You can book at most {limit} {unit}s at a time.' if requested > limit else '')
    sold_out = passengers > seats_left
    seats_required = kind == 'bus'

    rows = blank_rows(passengers, getattr(request.user, 'name', '') if request.method != 'POST' else '')
    form_ok = request.method == 'POST'
    if request.method == 'POST' and not closed and not error and not sold_out:
        rows, details_ok = read_passengers(request.POST, passengers)
        form_ok = details_ok
        for leg in legs:
            leg.chosen = in_layout_order(leg.item, leg.kind, request.POST.getlist(leg.field))
            leg.seat_problem = seat_error(leg.item, leg.kind, leg.chosen, passengers, seats_required, leg.taken)
            form_ok = form_ok and not leg.seat_problem
        if form_ok:
            booking, problem = _create_hold(request.user, legs, rows)
            if booking:
                return redirect('payments:choose_payment_method', booking_id=booking.id)
            if problem == 'seats':
                error = 'Someone else just booked those seats. Please try again.'
                for leg in legs:
                    leg.seats_left = seats_available(leg.item, leg.kind)
                seats_left = min(leg.seats_left for leg in legs)
                sold_out = passengers > seats_left
            else:
                error = 'Someone just took one of the seats you picked. Please pick again.'
                for leg in legs:
                    leg.taken = taken_seats(leg.item, leg.kind, exclude_booking=leg.own_id)
                    leg.chosen = [c for c in leg.chosen if c not in leg.taken]

    for leg in legs:
        leg.fare = leg.item.price * passengers
        leg.map = seat_layout(leg.item, leg.kind, leg.taken, leg.chosen)

    unit_total = sum(leg.item.price for leg in legs)
    return render(request, 'bookings/confirm_booking.html', {
        'item': item,
        'kind': kind,
        'legs': legs,
        'round_trip': bool(back),
        'item_type': kind.capitalize(),
        'unit': unit,
        'detail_url': f'{kind}_detail',
        'seats_available': seats_left,
        'max_pax': max(min(seats_left, limit), 1),
        'passengers': passengers,
        'return_id': back.pk if back else '',
        'total_price': unit_total * passengers,
        'closed': closed,
        'error': error,
        'sold_out': sold_out,
        'rows': rows,
        'genders': GENDERS,
        'seats_required': seats_required,
        'submitted': request.method == 'POST',
    })


def _create_hold(user, legs, rows):
    """Create (or update) the user's pending booking for every leg, checking seats under a
    lock so two people can't both take the last ones. Returns (first booking, problem);
    problem is 'seats' (not enough left), 'taken' (a chosen seat went) or ''."""
    count = len(rows)
    with transaction.atomic():
        # Lock the trips in a fixed order so two people booking the same pair can't deadlock.
        locked = {}
        for leg in sorted(legs, key=lambda l: (l.kind, l.item.pk)):
            locked[leg.index] = type(leg.item).objects.select_for_update().get(pk=leg.item.pk)

        plan = []
        for leg in legs:
            trip = locked[leg.index]
            existing = (
                Booking.objects.filter(user=user, status='pending', booking_type=leg.kind,
                                       booking_date__gte=hold_cutoff(), **{leg.kind: trip})
                .order_by('-booking_date').first()
            )
            free = seats_available(trip, leg.kind) + (existing.passengers if existing else 0)
            if count > free:
                return None, 'seats'
            taken = taken_seats(trip, leg.kind, exclude_booking=existing.pk if existing else None)
            if any(seat in taken for seat in leg.chosen):
                return None, 'taken'
            plan.append((leg, trip, existing))

        group = uuid.uuid4().hex if len(legs) > 1 else ''
        bookings = []
        for leg, trip, existing in plan:
            fields = dict(passengers=count, total_price=trip.price * count, group_ref=group,
                          leg=leg.role.lower() if group else '')
            if existing:  # same user clicked again: reuse their booking instead of holding twice
                for name, value in fields.items():
                    setattr(existing, name, value)
                existing.save(update_fields=list(fields))
                existing.travellers.all().delete()
                booking = existing
            else:
                booking = Booking.objects.create(
                    user=user, booking_type=leg.kind, status='pending', **{leg.kind: trip}, **fields,
                )
            Passenger.objects.bulk_create([
                Passenger(booking=booking, name=row['name'], age=int(row['age']), gender=row['gender'],
                          seat=leg.chosen[i] if i < len(leg.chosen) else '')
                for i, row in enumerate(rows)
            ])
            bookings.append(booking)
        return bookings[0], ''


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
    expire_stale(request.user)
    bookings = list(
        Booking.objects.filter(user=request.user)
        .select_related('flight', 'bus', 'hotel', 'room', 'review')
        .prefetch_related('travellers')
        .order_by('-booking_date')
    )
    for booking in bookings:
        booking.info = ticket_info(booking)
        booking.can_cancel = refund_for(booking)['allowed']
        booking.can_review = booking.status == 'confirmed' and trip_completed(booking)
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
    expire_stale(request.user)  # first, so a lapsed hold shows as cancelled
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
        'hold_expires': hold_expires_at(booking) if booking.status == 'pending' else None,
        'refund': refund_for(booking) if booking.status != 'cancelled' else None,
        'completed': trip_completed(booking),
        'can_review': booking.status == 'confirmed' and trip_completed(booking),
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
    booking = get_object_or_404(
        Booking.objects.select_related('flight', 'bus', 'hotel', 'room'),
        id=booking_id, user=request.user,
    )
    refund = refund_for(booking)

    if request.method == 'POST':
        if not refund['allowed']:
            messages.error(request, refund['reason'])
            return redirect('booking_detail', booking_id=booking.id)
        booking.status = 'cancelled'
        booking.cancelled_at = timezone.now()
        booking.refund_amount = refund['amount']
        booking.save()
        if refund['amount']:
            messages.success(request, f'Booking cancelled. \u20b9{refund["amount"]:,.0f} will be refunded to your original payment method.')
        else:
            messages.success(request, 'Booking cancelled.')
        return redirect('my_bookings')

    return render(request, 'bookings/cancel_booking.html', {
        'booking': booking,
        'info': ticket_info(booking),
        'refund': refund,
        'policy': POLICY_LABELS[booking.booking_type],
        'paid': booking.status == 'confirmed',
    })
