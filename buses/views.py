from django.shortcuts import render
from .models import Bus
from .forms import BusSearchForm


def bus_search_view(request):
    buses = []
    form = BusSearchForm(request.GET or None)

    if request.GET and form.is_valid():
        starting_location = form.cleaned_data['starting_location']
        destination = form.cleaned_data['destination']
        date = form.cleaned_data['date']

        buses = Bus.objects.filter(
            starting_location__iexact=starting_location,
            destination__iexact=destination,
            departure_time__date=date
        )

    return render(request, 'buses/search.html', {'form': form, 'buses': buses})