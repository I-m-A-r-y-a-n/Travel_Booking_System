from django.shortcuts import render, get_object_or_404
from .models import Room ,Hotel
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from bookings.models import Booking

def search_hotels(request):
    destination = request.GET.get('destination', '')
    guests = request.GET.get('guests', '')

    rooms = Room.objects.filter(available_rooms__gt=0)

    if destination:
        rooms = rooms.filter(hotel__location__icontains=destination)

    if guests:
        rooms = rooms.filter(capacity__gte=int(guests))

    # NOTE: check-in/check-out dates are not yet used to filter results.
    # Real date-based availability requires the Booking model to check
    # for overlapping reservations. This will be added once Booking exists.

    context = {
        'rooms': rooms,
        'destination': destination,
        'guests': guests,
    }
    return render(request, 'hotels/search_results.html', context)

def hotel_detail(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    rooms = hotel.rooms.all()

    context = {
        'hotel': hotel,
        'rooms': rooms,
    }
    return render(request, 'hotels/hotel_detail.html', context)

@login_required
def book_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if room.available_rooms < 1:
        return render(request, 'hotels/booking_failed.html', {'room': room})

    booking = Booking.objects.create(
        user=request.user,
        booking_type='hotel',
        hotel=room.hotel,
        total_price=room.price_per_night,
        status='pending',
    )

    room.available_rooms -= 1
    room.save()

    return redirect('payments:process_payment', booking_id=booking.id)