"""The search page logic that flights and buses share: one-way and round-trip search,
filters and sorting."""
from urllib.parse import urlencode

from django.shortcuts import render
from django.utils import timezone

from bookings.rules import booking_closed_reason
from bookings.utils import seats_available

from .filters import (
    FILTER_KEYS, TIME_BUCKETS, active_count, apply_filters, price_bounds, read_filters,
)


def search_trips(request, cfg):
    """`cfg` names the model, the form and the fields for this kind of trip."""
    model, kind = cfg['model'], cfg['kind']
    form = cfg['form'](request.GET or None)
    searched = bool(request.GET) and form.is_valid()
    passengers, items, outbound, bounds = 1, [], None, None
    round_trip = False
    filters = read_filters(request.GET, [c for c, _ in cfg.get('type_choices', [])])

    if searched:
        data = form.cleaned_data
        passengers = data['passengers']
        round_trip = data['trip'] == 'round'
        origin, dest, day = data[cfg['origin_field']], data[cfg['dest_field']], data['date']
        earliest = timezone.now()
        exact = False

        if round_trip and data.get('outbound'):
            outbound = model.objects.filter(pk=data['outbound']).first()
        if outbound is not None:
            # Step two of a round trip: the way back, after the outbound has arrived.
            origin, dest, day = getattr(outbound, cfg['dest_lookup']), getattr(outbound, cfg['origin_lookup']), data['return_date']
            earliest = max(earliest, outbound.arrival_time)
            exact = True

        suffix = 'iexact' if exact else 'icontains'
        items = list(
            model.objects.filter(
                **{f"{cfg['origin_lookup']}__{suffix}": origin, f"{cfg['dest_lookup']}__{suffix}": dest},
                departure_time__date=day, departure_time__gt=earliest,
            ).order_by('departure_time')
        )
        for item in items:
            item.seats_left = seats_available(item, kind)
            item.closed_reason = booking_closed_reason(item, kind)
            if outbound is not None:
                item.pair_total = (outbound.price + item.price) * passengers

        bounds = price_bounds(items)
        items = apply_filters(items, filters, bounds)
        sorter = cfg['sorters'].get(data['sort'])
        if sorter:
            items.sort(key=sorter)

    # Hidden fields so sorting and filtering keep the search (and the chosen outbound trip).
    carry = [(k, v) for k, values in request.GET.lists() if k not in FILTER_KEYS for v in values]
    select_qs = urlencode([(k, v) for k, v in carry if k != 'outbound'])

    return render(request, 'trips/search.html', {
        'kind': kind,
        'kind_label': cfg['kind_label'],
        'unit': cfg['unit'],
        'form': form,
        'origin_field': form[cfg['origin_field']],
        'dest_field': form[cfg['dest_field']],
        'items': items,
        'searched': searched,
        'has_errors': bool(request.GET) and not searched,
        'passengers': passengers,
        'cities': cfg['cities'](),
        'detail_url': cfg['detail_url'],
        'book_url': cfg['book_url'],
        'round_trip': round_trip,
        'outbound': outbound,
        'step': 2 if outbound is not None else 1,
        'filters': filters,
        'bounds': bounds,
        'filters_on': active_count(filters, bounds),
        'time_buckets': TIME_BUCKETS,
        'type_choices': cfg.get('type_choices', []),
        'carry': carry,
        'select_qs': select_qs,
        'max_price_value': filters['max_price'] if filters['max_price'] is not None else (bounds['max'] if bounds else 0),
    })
