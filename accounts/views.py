from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.hashers import make_password
from .forms import UserRegistrationForm, UserLoginForm
from django.contrib.auth.decorators import login_required
from bookings.models import Booking

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = form.cleaned_data['email']
            user.password = make_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    error = None
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard_placeholder')
            else:
                error = 'Invalid email or password'
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form, 'error': error})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_placeholder(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')

    hotel_bookings = bookings.filter(booking_type='hotel')
    flight_bookings = bookings.filter(booking_type='flight')
    bus_bookings = bookings.filter(booking_type='bus')

    context = {
        'hotel_bookings': hotel_bookings,
        'flight_bookings': flight_bookings,
        'bus_bookings': bus_bookings,
    }
    return render(request, 'accounts/dashboard_placeholder.html', context)