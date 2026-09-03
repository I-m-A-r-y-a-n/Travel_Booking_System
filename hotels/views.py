from django.shortcuts import render, get_object_or_404
from .models import Room ,Hotel

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