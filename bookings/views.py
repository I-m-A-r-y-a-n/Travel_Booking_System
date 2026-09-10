from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from flights.models import Flight
from buses.models import Bus
from .models import Booking


@login_required
def book_flight_view(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    seats_booked = Booking.objects.filter(flight=flight, status='confirmed').count()
    seats_available = flight.total_seats - seats_booked

    if request.method == 'POST':
        if seats_available > 0:
            Booking.objects.create(
                user=request.user,
                booking_type='flight',
                flight=flight,
                total_price=flight.price,
                status='confirmed'
            )
            return redirect('my_bookings')
        else:
            return render(request, 'bookings/confirm_booking.html', {
                'item': flight, 'item_type': 'Flight', 'sold_out': True
            })

    return render(request, 'bookings/confirm_booking.html', {
        'item': flight, 'item_type': 'Flight', 'seats_available': seats_available
    })


@login_required
def book_bus_view(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id)
    seats_booked = Booking.objects.filter(bus=bus, status='confirmed').count()
    seats_available = bus.total_seats - seats_booked

    if request.method == 'POST':
        if seats_available > 0:
            Booking.objects.create(
                user=request.user,
                booking_type='bus',
                bus=bus,
                total_price=bus.price,
                status='confirmed'
            )
            return redirect('my_bookings')
        else:
            return render(request, 'bookings/confirm_booking.html', {
                'item': bus, 'item_type': 'Bus', 'sold_out': True
            })

    return render(request, 'bookings/confirm_booking.html', {
        'item': bus, 'item_type': 'Bus', 'seats_available': seats_available
    })


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