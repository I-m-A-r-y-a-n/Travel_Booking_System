from django.shortcuts import get_object_or_404, render

from bookings.rules import booking_closed_reason, max_per_booking
from bookings.utils import seats_available
from reviews.utils import review_summary
from travelbooking.helpers import parse_int
from travelbooking.trips import search_trips

from .forms import FlightSearchForm
from .models import Flight

SORTERS = {
    'price': lambda f: f.price,
    'duration': lambda f: f.duration_minutes,
}


def _known_cities():
    cities = set(Flight.objects.values_list('departure_city', flat=True))
    cities |= set(Flight.objects.values_list('destination_city', flat=True))
    return sorted(cities)


def flight_search_view(request):
    return search_trips(request, {
        'model': Flight, 'kind': 'flight', 'kind_label': 'Flights', 'unit': 'passenger',
        'form': FlightSearchForm, 'sorters': SORTERS, 'cities': _known_cities,
        'origin_field': 'departure_city', 'dest_field': 'destination_city',
        'origin_lookup': 'departure_city', 'dest_lookup': 'destination_city',
        'detail_url': 'flight_detail', 'book_url': 'book_flight',
    })


def flight_detail_view(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    seats_left = seats_available(flight, 'flight')
    limit = max_per_booking('flight')
    passengers = min(parse_int(request.GET.get('passengers'), default=1, minimum=1), limit)

    return render(request, 'trips/detail.html', {
        'kind': 'flight',
        'kind_label': 'Flight',
        'unit': 'passenger',
        'item': flight,
        'seats_left': seats_left,
        'passengers': passengers,
        'total_price': flight.price * passengers,
        'sold_out': seats_left < 1,
        'closed': booking_closed_reason(flight, 'flight'),
        'max_pax': max(min(seats_left, limit), 1),
        'too_many': passengers > seats_left,
        'reviews': review_summary('flight', flight),
        'search_url': 'flight_search',
        'book_url': 'book_flight',
    })
