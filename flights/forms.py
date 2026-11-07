from django import forms

SORT_CHOICES = [
    ('', 'Earliest departure'),
    ('price', 'Price: low to high'),
    ('duration', 'Shortest duration'),
]


class FlightSearchForm(forms.Form):
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
    date = forms.DateField(label='Departure date', widget=forms.DateInput(attrs={'type': 'date'}))
    passengers = forms.IntegerField(min_value=1, initial=1, label='Passengers')
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False, label='Sort by')