from django.shortcuts import render

# Create your views here.
import random
from django.shortcuts import render, get_object_or_404
from bookings.models import Booking
from .models import Payment

def process_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # MOCK PAYMENT LOGIC (no real gateway).
    # Simulates a payment attempt with a random outcome, since the SRS
    # explicitly excludes real payment gateway integration.
    method = request.GET.get('method', 'CARD')
    is_success = random.choice([True, False])

    payment = Payment.objects.create(
        booking=booking,
        payment_method=method,
        amount=booking.total_price,
        status='SUCCESS' if is_success else 'FAILED',
    )

    if is_success:
        booking.status = 'confirmed'
    else:
        booking.status = 'cancelled'
    booking.save()

    context = {
        'payment': payment,
        'booking': booking,
    }
    return render(request, 'payments/payment_result.html', context)