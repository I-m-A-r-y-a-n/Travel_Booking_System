from django.shortcuts import render
from .models import Flight
from .forms import FlightSearchForm


def flight_search_view(request):
    flights = []
    form = FlightSearchForm(request.GET or None)

    if request.GET and form.is_valid():
        departure_city = form.cleaned_data['departure_city']
        destination_city = form.cleaned_data['destination_city']
        date = form.cleaned_data['date']

        flights = Flight.objects.filter(
            departure_city__iexact=departure_city,
            destination_city__iexact=destination_city,
            departure_time__date=date
        )

    return render(request, 'flights/search.html', {'form': form, 'flights': flights})