from django.shortcuts import get_object_or_404, render

from bookings.utils import seats_available
from reviews.utils import review_summary
from travelbooking.helpers import parse_int

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
    buses = []
    form = BusSearchForm(request.GET or None)
    searched = bool(request.GET) and form.is_valid()
    passengers = 1

    if searched:
        data = form.cleaned_data
        passengers = data['passengers']

        buses = list(
            Bus.objects.filter(
                starting_location__icontains=data['starting_location'],
                destination__icontains=data['destination'],
                departure_time__date=data['date'],
            ).order_by('departure_time')
        )
        for bus in buses:
            bus.seats_left = seats_available(bus, 'bus')

        sorter = SORTERS.get(data['sort'])
        if sorter:
            buses.sort(key=sorter)

    return render(request, 'trips/search.html', {
        'kind': 'bus',
        'kind_label': 'Buses',
        'unit': 'seat',
        'form': form,
        'origin_field': form['starting_location'],
        'dest_field': form['destination'],
        'items': buses,
        'searched': searched,
        'has_errors': bool(request.GET) and not searched,
        'passengers': passengers,
        'cities': _known_cities(),
        'detail_url': 'bus_detail',
        'book_url': 'book_bus',
    })


def bus_detail_view(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id)
    seats_left = seats_available(bus, 'bus')
    passengers = parse_int(request.GET.get('passengers'), default=1, minimum=1)

    return render(request, 'trips/detail.html', {
        'kind': 'bus',
        'kind_label': 'Bus',
        'unit': 'seat',
        'item': bus,
        'seats_left': seats_left,
        'passengers': passengers,
        'total_price': bus.price * passengers,
        'sold_out': seats_left < 1,
        'too_many': passengers > seats_left,
        'reviews': review_summary('bus', bus),
        'search_url': 'bus_search',
        'book_url': 'book_bus',
    })
