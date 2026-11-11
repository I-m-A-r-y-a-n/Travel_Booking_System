import random

from django.contrib import messages
from django.db import transaction

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from bookings.models import Booking
from bookings.rules import HOLD_MINUTES, expire_stale, group_of, hold_expires_at, is_hold_expired
from bookings.tickets import ticket_info
from .models import Payment

# Payment is simulated (no real gateway): this share of attempts succeeds.
SUCCESS_RATE = 0.90

METHODS = [
    {'value': 'CARD', 'label': 'Credit / Debit card', 'hint': 'Visa, Mastercard, RuPay and more', 'icon': 'card'},
    {'value': 'UPI', 'label': 'UPI', 'hint': 'Pay with any UPI app', 'icon': 'phone'},
    {'value': 'NETBANKING', 'label': 'Net banking', 'hint': 'All major Indian banks', 'icon': 'bank'},
]
VALID_METHODS = {m['value'] for m in METHODS}


@login_required
def choose_payment_method(request, booking_id):
    expire_stale(request.user)
    booking = get_object_or_404(
        Booking.objects.select_related('flight', 'bus', 'hotel', 'room'),
        id=booking_id, user=request.user,
    )

    if booking.status != 'pending':
        if booking.status == 'cancelled':
            messages.error(request, 'This booking was cancelled or its payment time ran out. Please search again.')
        return redirect('my_bookings')

    expires = hold_expires_at(booking)
    group = [b for b in group_of(booking) if b.status == 'pending']
    return render(request, 'payments/choose_method.html', {
        'booking': booking,
        'info': ticket_info(booking),
        'legs': [ticket_info(b) for b in group],
        'amount': sum(b.total_price for b in group),
        'methods': METHODS,
        'selected': 'CARD',
        'hold_minutes': HOLD_MINUTES,
        'expires_at': expires,
        'seconds_left': max(int((expires - timezone.now()).total_seconds()), 0),
    })


@login_required
def process_payment(request, booking_id):
    if request.method != 'POST':
        return redirect('payments:choose_payment_method', booking_id=booking_id)

    with transaction.atomic():
        # Lock the booking so a double click (or two tabs) can't pay for it twice.
        booking = get_object_or_404(
            Booking.objects.select_for_update(), id=booking_id, user=request.user,
        )
        if booking.status != 'pending':
            return redirect('my_bookings')

        group = [b for b in group_of(booking, lock=True) if b.status == 'pending']
        if any(is_hold_expired(b) for b in group):
            for b in group:
                b.status = 'cancelled'
                b.save(update_fields=['status'])
            messages.error(request, 'Your payment time ran out and the seats were released. Please book again.')
            return redirect('my_bookings')

        # MOCK PAYMENT LOGIC (no real gateway).
        method = request.POST.get('method', 'CARD')
        if method not in VALID_METHODS:
            method = 'CARD'
        is_success = random.random() < SUCCESS_RATE

        # A round trip is paid in one go: every leg gets its own payment record, all with
        # the same outcome. A failed payment keeps the seats on hold so the user can try
        # again until the hold runs out, like the real sites. Only success confirms them.
        payment = None
        for b in group:
            made = Payment.objects.create(
                booking=b,
                payment_method=method,
                amount=b.total_price,
                status='SUCCESS' if is_success else 'FAILED',
            )
            if b.pk == booking.pk:
                payment = made
            if is_success:
                b.status = 'confirmed'
                b.save(update_fields=['status'])

    # Redirect (instead of rendering here) so refreshing the result page can't resubmit the payment.
    return redirect('payments:payment_result', payment_id=payment.id)


@login_required
def payment_result(request, payment_id):
    payment = get_object_or_404(
        Payment.objects.select_related('booking'),
        id=payment_id, booking__user=request.user,
    )
    booking = payment.booking
    return render(request, 'payments/payment_result.html', {
        'payment': payment,
        'booking': booking,
        'info': ticket_info(booking),
        'success': payment.status == 'SUCCESS',
        'can_retry': booking.status == 'pending' and not is_hold_expired(booking),
        'others': [ticket_info(b) for b in group_of(booking) if b.pk != booking.pk],
        'hold_minutes': HOLD_MINUTES,
    })
