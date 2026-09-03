from django import forms


class BusSearchForm(forms.Form):
    starting_location = forms.CharField(max_length=100)
    destination = forms.CharField(max_length=100)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    passengers = forms.IntegerField(min_value=1, initial=1)