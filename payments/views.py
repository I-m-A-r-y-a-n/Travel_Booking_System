import random

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from bookings.models import Booking
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
    booking = get_object_or_404(
        Booking.objects.select_related('flight', 'bus', 'hotel', 'room'),
        id=booking_id, user=request.user,
    )

    if booking.status != 'pending':
        return redirect('my_bookings')

    return render(request, 'payments/choose_method.html', {
        'booking': booking,
        'info': ticket_info(booking),
        'methods': METHODS,
        'selected': 'CARD',
    })


@login_required
def process_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if booking.status != 'pending':
        return redirect('my_bookings')

    if request.method != 'POST':
        return redirect('payments:choose_payment_method', booking_id=booking.id)

    # MOCK PAYMENT LOGIC (no real gateway).
    method = request.POST.get('method', 'CARD')
    if method not in VALID_METHODS:
        method = 'CARD'
    is_success = random.random() < SUCCESS_RATE

    payment = Payment.objects.create(
        booking=booking,
        payment_method=method,
        amount=booking.total_price,
        status='SUCCESS' if is_success else 'FAILED',
    )

    booking.status = 'confirmed' if is_success else 'cancelled'
    booking.save()

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
    })
