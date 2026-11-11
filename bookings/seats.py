"""Seat maps for flights and buses, and checks on the seats a person picks.

Flights: rows of 6 (A-F) with an aisle after C.  Seater buses: rows of 4 with an aisle
after B.  Sleeper buses: a lower and an upper deck of berths (two on one side, one on
the other).  The map is built from the trip's total_seats, so it always matches.
"""
import math

from .models import Booking, Passenger
from .rules import holding_q

SLEEPER_TYPES = {'AC_SLEEPER', 'NONAC_SLEEPER'}


def _labels_by_row(total, letters):
    """Rows like [['1A','1B','1C'], ['1D','1E','1F']] cut off after `total` seats."""
    rows, number, made = [], 1, 0
    while made < total:
        row = []
        for letter in letters:
            if made >= total:
                break
            row.append(f'{number}{letter}')
            made += 1
        rows.append(row)
        number += 1
    return rows


def _chunk(labels, size):
    return [labels[i:i + size] for i in range(0, len(labels), size)]


def _decks(item, kind):
    """[(deck name, left seats, right seats, labels in order)]"""
    total = item.total_seats
    if kind == 'flight':
        labels = [l for row in _labels_by_row(total, "ABCDEF") for l in row]
        return [('', 3, 3, labels)]
    if getattr(item, 'bus_type', '') in SLEEPER_TYPES:
        lower = math.ceil(total / 2)
        return [
            ('Lower deck', 2, 1, [f'L{n}' for n in range(1, lower + 1)]),
            ('Upper deck', 2, 1, [f'U{n}' for n in range(1, total - lower + 1)]),
        ]
    labels = [l for row in _labels_by_row(total, "ABCD") for l in row]
    return [('', 2, 2, labels)]


def all_labels(item, kind):
    return [label for _, _, _, labels in _decks(item, kind) for label in labels]


def taken_seats(item, kind, exclude_booking=None):
    """Seats already held by confirmed bookings, or unpaid ones still inside their hold."""
    holding = Booking.objects.filter(holding_q(), **{kind: item})
    if exclude_booking is not None:
        holding = holding.exclude(pk=exclude_booking)
    return set(
        Passenger.objects.filter(booking__in=holding).exclude(seat='').values_list('seat', flat=True)
    )


def seat_layout(item, kind, taken=None, chosen=()):
    """Everything the template needs to draw the seat map."""
    taken = taken if taken is not None else taken_seats(item, kind)
    chosen = set(chosen)
    decks = []
    for name, left, right, labels in _decks(item, kind):
        rows = []
        for number, row in enumerate(_chunk(labels, left + right), start=1):
            cells = [{'label': l, 'taken': l in taken, 'chosen': l in chosen} for l in row]
            # Pad a short last row so the seats stay under their own columns.
            left_cells = cells[:left]
            right_cells = cells[left:]
            left_cells += [None] * (left - len(left_cells))
            right_cells += [None] * (right - len(right_cells))
            rows.append({'num': number, 'left': left_cells, 'right': right_cells})
        decks.append({'name': name, 'rows': rows})
    free = len(all_labels(item, kind)) - len(taken & set(all_labels(item, kind)))
    return {'decks': decks, 'free': free}


def seat_error(item, kind, chosen, count, required, taken):
    """A message if the picked seats are unusable, else ''."""
    if not chosen:
        return f'Please choose {count} seat{"s" if count != 1 else ""}.' if required else ''
    if len(chosen) != count:
        return f'Please choose exactly {count} seat{"s" if count != 1 else ""} (you chose {len(chosen)}).'
    valid = set(all_labels(item, kind))
    if len(set(chosen)) != len(chosen) or any(c not in valid for c in chosen):
        return 'One of the chosen seats is not valid. Please pick again.'
    if any(c in taken for c in chosen):
        return 'Someone just took one of those seats. Please pick again.'
    return ''


def in_layout_order(item, kind, chosen):
    order = {label: i for i, label in enumerate(all_labels(item, kind))}
    return sorted(set(chosen), key=lambda l: order.get(l, 10 ** 6))
