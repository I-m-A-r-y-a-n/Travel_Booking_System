"""Result filters shared by the flight and bus search pages: non-stop, departure time,
price range (and bus type). Read from the query string, applied in Python."""
from django.utils import timezone

# key, label, first hour, last hour (exclusive)
TIME_BUCKETS = [
    ('early', 'Before 6 AM', 0, 6),
    ('morning', '6 AM to 12 PM', 6, 12),
    ('afternoon', '12 PM to 6 PM', 12, 18),
    ('evening', 'After 6 PM', 18, 24),
]
BUCKET_KEYS = {key for key, *_ in TIME_BUCKETS}

# Keys that belong to the filter bar (the rest of the query string is the search itself).
FILTER_KEYS = ('nonstop', 'max_price', 'dep', 'bus_type', 'sort')


def read_filters(get, bus_types=()):
    max_price = (get.get('max_price') or '').strip()
    return {
        'nonstop': get.get('nonstop') == '1',
        'max_price': int(max_price) if max_price.isdigit() else None,
        'dep': [k for k in get.getlist('dep') if k in BUCKET_KEYS],
        'bus_type': [t for t in get.getlist('bus_type') if t in set(bus_types)],
    }


def price_bounds(items):
    prices = [int(i.price) for i in items]
    if not prices:
        return None
    low, high = min(prices), max(prices)
    # Round to tidy slider ends (nearest 100).
    return {'min': low // 100 * 100, 'max': -(-high // 100) * 100}


def _bucket(item):
    hour = timezone.localtime(item.departure_time).hour
    return next(key for key, _, start, end in TIME_BUCKETS if start <= hour < end)


def apply_filters(items, f, bounds=None):
    out = []
    for item in items:
        if f['nonstop'] and getattr(item, 'stops', 0):
            continue
        if f['max_price'] is not None and (bounds is None or f['max_price'] < bounds['max']) and item.price > f['max_price']:
            continue
        if f['dep'] and _bucket(item) not in f['dep']:
            continue
        if f['bus_type'] and getattr(item, 'bus_type', None) not in f['bus_type']:
            continue
        out.append(item)
    return out


def active_count(f, bounds=None):
    count = int(f['nonstop']) + len(f['dep']) + len(f['bus_type'])
    if f['max_price'] is not None and bounds and f['max_price'] < bounds['max']:
        count += 1
    return count
