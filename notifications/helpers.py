"""Presentation helpers for notifications.

The stored message mentions the booking number ("Booking #20 ..."). For display we turn
that into a friendly title and text built from the booking itself (route or hotel), and
keep the number only to work out which booking page the notification should open.
"""
import re

from django.urls import reverse

from bookings.models import Booking
from bookings.tickets import ticket_info

_BOOKING_REF = re.compile(r'#(\d+)')
_AMOUNT = re.compile(r'Rs\.?\s*([\d,]+(?:\.\d+)?)')


def _event(notification):
    text = (notification.message or '').lower()
    kind = notification.notification_type
    if kind == 'cancellation':
        return 'cancelled'
    if kind == 'payment_confirmation':
        return 'pay_ok' if 'success' in text else 'pay_fail'
    return 'confirmed' if 'confirmed' in text else 'placed'


_STYLE = {
    'placed': ('Booking started', 'ticket', 'info'),
    'confirmed': ('Booking confirmed', 'check-circle', 'ok'),
    'cancelled': ('Booking cancelled', 'x-circle', 'bad'),
    'pay_ok': ('Payment successful', 'rupee', 'ok'),
    'pay_fail': ('Payment failed', 'x-circle', 'bad'),
}


def _route(info):
    """'Bangalore → Delhi' for trips, 'Hotel, City' for stays."""
    if info['kind'] == 'hotel':
        return info['summary'] or info['title']
    return f"{info['origin']} → {info['dest']}"


def _text(event, info, amount):
    what = _route(info) if info else 'your booking'
    noun = {'flight': 'flight', 'bus': 'bus', 'hotel': 'stay'}.get(info['kind'], 'booking') if info else 'booking'
    if event == 'placed':
        return f'Your {noun} {what} is waiting for payment.' if info else 'Your booking is waiting for payment.'
    if event == 'confirmed':
        return f'{what} is confirmed. Have a great trip!' if info else 'Your booking is confirmed. Have a great trip!'
    if event == 'cancelled':
        return f'Your {noun} {what} was cancelled.' if info else 'Your booking was cancelled.'
    paid = f'₹{amount} ' if amount else ''
    if event == 'pay_ok':
        return f'{paid}paid for {what}.'.strip().capitalize() if not info else f'{paid}paid for {what}.'
    return f'{paid}for {what} was not completed.'.strip() if info else 'Your payment was not completed.'


def decorate_all(notifications, user=None):
    """Add .title, .text, .icon, .tone and .link to each notification."""
    notifications = list(notifications)
    ids = set()
    for n in notifications:
        m = _BOOKING_REF.search(n.message or '')
        n.booking_id_ref = int(m.group(1)) if m else None
        if n.booking_id_ref:
            ids.add(n.booking_id_ref)
    bookings = {}
    if ids:
        qs = Booking.objects.filter(id__in=ids).select_related('flight', 'bus', 'hotel', 'room')
        if user is not None:
            qs = qs.filter(user=user)
        bookings = {b.id: b for b in qs}

    for n in notifications:
        event = _event(n)
        title, icon, tone = _STYLE[event]
        booking = bookings.get(n.booking_id_ref)
        info = ticket_info(booking) if booking else None
        amount = None
        m = _AMOUNT.search(n.message or '')
        if m:
            value = float(m.group(1).replace(',', ''))
            amount = f'{value:,.0f}' if value == int(value) else f'{value:,.2f}'
        n.title, n.icon, n.tone = title, icon, tone
        n.text = _text(event, info, amount)
        n.link = reverse('booking_detail', args=[booking.id]) if booking else ''
    return notifications


def decorate(notification, user=None):
    return decorate_all([notification], user)[0]
