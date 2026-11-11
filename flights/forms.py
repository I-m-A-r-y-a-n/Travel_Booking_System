from django import forms

from travelbooking.searchforms import TripSearchForm


class FlightSearchForm(TripSearchForm):
    departure_city = forms.CharField(
        max_length=100,
        label='From',
        widget=forms.TextInput(attrs={'placeholder': 'Bangalore', 'list': 'city-list', 'autocomplete': 'off'}),
    )
    destination_city = forms.CharField(
        max_length=100,
        label='To',
        widget=forms.TextInput(attrs={'placeholder': 'Delhi', 'list': 'city-list', 'autocomplete': 'off'}),
    )
