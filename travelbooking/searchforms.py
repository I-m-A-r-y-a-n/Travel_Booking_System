"""The parts of the flight and bus search forms that are the same: date, return date,
passengers, sorting and the filters."""
from django import forms
from django.utils import timezone

from bookings.rules import search_date_error

SORT_CHOICES = [
    ('', 'Earliest departure'),
    ('price', 'Price: low to high'),
    ('duration', 'Shortest duration'),
]


class TripSearchForm(forms.Form):
    date = forms.DateField(label='Departure date', widget=forms.DateInput(attrs={'type': 'date'}))
    return_date = forms.DateField(required=False, label='Return date', widget=forms.DateInput(attrs={'type': 'date'}))
    trip = forms.ChoiceField(choices=[('oneway', 'One way'), ('round', 'Round trip')], required=False)
    outbound = forms.IntegerField(required=False, min_value=1)  # set once an outbound trip is chosen
    passengers = forms.IntegerField(min_value=1, initial=1, label='Passengers')
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False, label='Sort by')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate().isoformat()
        # Browsers then grey out past days in the date pickers (the server checks again).
        self.fields['date'].widget.attrs['min'] = today
        self.fields['return_date'].widget.attrs['min'] = today

    def clean_date(self):
        value = self.cleaned_data['date']
        problem = search_date_error(value)
        if problem:
            raise forms.ValidationError(problem)
        return value

    def clean(self):
        data = super().clean()
        trip = data.get('trip') or ('round' if data.get('return_date') else 'oneway')
        data['trip'] = trip
        if trip == 'round':
            back, going = data.get('return_date'), data.get('date')
            if not back:
                self.add_error('return_date', 'Choose a return date for a round trip.')
            elif going and back < going:
                self.add_error('return_date', 'The return date cannot be before the departure date.')
            else:
                problem = search_date_error(back)
                if problem:
                    self.add_error('return_date', problem)
        else:
            data['return_date'] = None
        return data
