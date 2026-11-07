from django import forms

SORT_CHOICES = [
    ('', 'Earliest departure'),
    ('price', 'Price: low to high'),
    ('duration', 'Shortest duration'),
]


class BusSearchForm(forms.Form):
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
    date = forms.DateField(label='Travel date', widget=forms.DateInput(attrs={'type': 'date'}))
    passengers = forms.IntegerField(min_value=1, initial=1, label='Passengers')
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False, label='Sort by')
