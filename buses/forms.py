from django import forms

from travelbooking.searchforms import TripSearchForm


class BusSearchForm(TripSearchForm):
    starting_location = forms.CharField(
        max_length=100,
        label='From',
        widget=forms.TextInput(attrs={'placeholder': 'Chennai', 'list': 'city-list', 'autocomplete': 'off'}),
    )
    destination = forms.CharField(
        max_length=100,
        label='To',
        widget=forms.TextInput(attrs={'placeholder': 'Bangalore', 'list': 'city-list', 'autocomplete': 'off'}),
    )
