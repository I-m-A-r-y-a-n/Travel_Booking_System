from django.shortcuts import get_object_or_404, render

from bookings.rules import booking_closed_reason, max_per_booking
from bookings.utils import seats_available
from reviews.utils import review_summary
from travelbooking.helpers import parse_int
from travelbooking.trips import search_trips

from .forms import BusSearchForm
from .models import Bus

SORTERS = {
    'price': lambda b: b.price,
    'duration': lambda b: b.duration_minutes,
}


def _known_cities():
    cities = set(Bus.objects.values_list('starting_location', flat=True))
    cities |= set(Bus.objects.values_list('destination', flat=True))
    return sorted(cities)


def bus_search_view(request):
    return search_trips(request, {
        'model': Bus, 'kind': 'bus', 'kind_label': 'Buses', 'unit': 'seat',
        'form': BusSearchForm, 'sorters': SORTERS, 'cities': _known_cities,
        'origin_field': 'starting_location', 'dest_field': 'destination',
        'origin_lookup': 'starting_location', 'dest_lookup': 'destination',
        'detail_url': 'bus_detail', 'book_url': 'book_bus',
        'type_choices': [('AC_SEATER', 'AC Seater'), ('NONAC_SEATER', 'Non-AC Seater'),
                         ('AC_SLEEPER', 'AC Sleeper'), ('NONAC_SLEEPER', 'Non-AC Sleeper'),
                         ('VOLVO', 'Volvo Multi-Axle')],
    })


def bus_detail_view(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id)
    seats_left = seats_available(bus, 'bus')
    limit = max_per_booking('bus')
    passengers = min(parse_int(request.GET.get('passengers'), default=1, minimum=1), limit)

    return render(request, 'trips/detail.html', {
        'kind': 'bus',
        'kind_label': 'Bus',
        'unit': 'seat',
        'item': bus,
        'seats_left': seats_left,
        'passengers': passengers,
        'total_price': bus.price * passengers,
        'sold_out': seats_left < 1,
        'closed': booking_closed_reason(bus, 'bus'),
        'max_pax': max(min(seats_left, limit), 1),
        'too_many': passengers > seats_left,
        'reviews': review_summary('bus', bus),
        'search_url': 'bus_search',
        'book_url': 'book_bus',
    })
