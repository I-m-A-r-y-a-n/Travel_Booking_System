from django.shortcuts import render, get_object_or_404
from .models import Room ,Hotel
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from bookings.models import Booking
from datetime import datetime

def search_hotels(request):
    destination = request.GET.get('destination', '')
    guests = request.GET.get('guests', '')
    check_in = request.GET.get('check_in', '')
    check_out = request.GET.get('check_out', '')

    rooms = Room.objects.all()

    if destination:
        rooms = rooms.filter(hotel__location__icontains=destination)

    if guests:
        rooms = rooms.filter(capacity__gte=int(guests))

    available_rooms_list = []

    if check_in and check_out:
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()

        for room in rooms:
            overlapping = Booking.objects.filter(
                room=room,
                status__in=['pending', 'confirmed'],
                check_in_date__lt=check_out_date,
                check_out_date__gt=check_in_date,
            ).count()

            if overlapping < room.total_rooms:
                available_rooms_list.append(room)
    else:
        # No dates provided yet - fall back to showing all matching rooms
        available_rooms_list = list(rooms)

    context = {
        'rooms': available_rooms_list,
        'destination': destination,
        'guests': guests,
        'check_in': check_in,
        'check_out': check_out,
    }
    return render(request, 'hotels/search_results.html', context)

def hotel_detail(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    rooms = hotel.rooms.all()
    check_in = request.GET.get('check_in', '')
    check_out = request.GET.get('check_out', '')

    context = {
        'hotel': hotel,
        'rooms': rooms,
        'check_in': check_in,
        'check_out': check_out,
    }
    return render(request, 'hotels/hotel_detail.html', context)

@login_required
def book_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')

    if not check_in or not check_out:
        return render(request, 'hotels/booking_failed.html', {
            'room': room,
            'reason': 'Please select check-in and check-out dates before booking.'
        })

    check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
    check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()

    if check_out_date <= check_in_date:
        return render(request, 'hotels/booking_failed.html', {
            'room': room,
            'reason': 'Check-out date must be after check-in date.'
        })

    overlapping = Booking.objects.filter(
        room=room,
        status__in=['pending', 'confirmed'],
        check_in_date__lt=check_out_date,
        check_out_date__gt=check_in_date,
    ).count()

    if overlapping >= room.total_rooms:
        return render(request, 'hotels/booking_failed.html', {
            'room': room,
            'reason': 'No rooms available for the selected dates.'
        })

    nights = (check_out_date - check_in_date).days
    total_price = room.price_per_night * nights

    booking = Booking.objects.create(
        user=request.user,
        booking_type='hotel',
        hotel=room.hotel,
        room=room,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        total_price=total_price,
        status='pending',
    )

    return redirect('payments:choose_payment_method', booking_id=booking.id)