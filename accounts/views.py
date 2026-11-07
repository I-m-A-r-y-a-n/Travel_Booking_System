from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import UserRegistrationForm, UserLoginForm


def _safe_next(request):
    """The page the user was trying to reach before being asked to log in.

    Only same-site addresses are accepted, so a crafted ?next=https://evil.example
    link can't send people to another website after they log in.
    """
    target = request.POST.get('next') or request.GET.get('next') or ''
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return target
    return ''


def register_view(request):
    next_url = _safe_next(request)
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = form.cleaned_data['email']
            user.password = make_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Account created. Please log in to continue.')
            login_url = reverse('login')
            if next_url:
                login_url += '?' + urlencode({'next': next_url})
            return redirect(login_url)
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form, 'next': next_url})


def login_view(request):
    next_url = _safe_next(request)
    if request.user.is_authenticated and request.method == 'GET':
        return redirect(next_url or 'home')

    error = None
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                # Back to where they were heading (e.g. the booking page), else the dashboard.
                return redirect(next_url or 'home')
            error = 'Invalid email or password'
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form, 'error': error, 'next': next_url})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_placeholder(request):
    """Old dashboard address. The home page is the landing page now, so just go there."""
    return redirect('home')


def home_view(request):
    return render(request, 'home.html')
