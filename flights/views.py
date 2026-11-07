from django.shortcuts import get_object_or_404, render

from bookings.utils import seats_available
from reviews.utils import review_summary
from travelbooking.helpers import parse_int

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
    flights = []
    form = FlightSearchForm(request.GET or None)
    searched = bool(request.GET) and form.is_valid()
    passengers = 1

    if searched:
        data = form.cleaned_data
        passengers = data['passengers']

        flights = list(
            Flight.objects.filter(
                departure_city__icontains=data['departure_city'],
                destination_city__icontains=data['destination_city'],
                departure_time__date=data['date'],
            ).order_by('departure_time')
        )
        for flight in flights:
            flight.seats_left = seats_available(flight, 'flight')

        sorter = SORTERS.get(data['sort'])
        if sorter:
            flights.sort(key=sorter)

    return render(request, 'trips/search.html', {
        'kind': 'flight',
        'kind_label': 'Flights',
        'unit': 'passenger',
        'form': form,
        'origin_field': form['departure_city'],
        'dest_field': form['destination_city'],
        'items': flights,
        'searched': searched,
        'has_errors': bool(request.GET) and not searched,
        'passengers': passengers,
        'cities': _known_cities(),
        'detail_url': 'flight_detail',
        'book_url': 'book_flight',
    })


def flight_detail_view(request, flight_id):
    flight = get_object_or_404(Flight, id=flight_id)
    seats_left = seats_available(flight, 'flight')
    passengers = parse_int(request.GET.get('passengers'), default=1, minimum=1)

    return render(request, 'trips/detail.html', {
        'kind': 'flight',
        'kind_label': 'Flight',
        'unit': 'passenger',
        'item': flight,
        'seats_left': seats_left,
        'passengers': passengers,
        'total_price': flight.price * passengers,
        'sold_out': seats_left < 1,
        'too_many': passengers > seats_left,
        'reviews': review_summary('flight', flight),
        'search_url': 'flight_search',
        'book_url': 'book_flight',
    })