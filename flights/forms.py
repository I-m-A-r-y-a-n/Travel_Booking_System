from django import forms


class FlightSearchForm(forms.Form):
    departure_city = forms.CharField(max_length=100)
    destination_city = forms.CharField(max_length=100)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    passengers = forms.IntegerField(min_value=1, initial=1)