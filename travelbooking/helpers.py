"""Small, dependency-free helpers shared by the flights, buses and hotels apps."""
import re
from datetime import datetime

# (regex, icon id). The first match wins, so order matters. The icon ids refer to
# the <symbol> sprite defined in templates/base.html. Anything unmatched gets "check".
_AMENITY_ICONS = [
    (r'wi-?fi|internet', 'wifi'),
    (r'\bac\b|a/c|air[- ]?condition|cooling', 'wind'),
    (r'parking', 'parking'),
    (r'pool', 'waves'),
    (r'gym|fitness', 'activity'),
    (r'\bspa\b|massage|wellness', 'heart'),
    (r'room service|reception|front desk|concierge', 'bell'),
    (r'meal|breakfast|lunch|dinner|restaurant|food|snack|dining|kitchen', 'utensils'),
    (r'water|drink|beverage', 'droplet'),
    (r'charg|power|usb|socket', 'zap'),
    (r'\btv\b|television|entertainment', 'tv'),
    (r'baggage|luggage|\bbag', 'briefcase'),
    (r'track|gps', 'navigation'),
    (r'light|lamp', 'bulb'),
    (r'blanket|pillow|sleeper|bed', 'bed'),
    (r'cancel|refund|insurance|safe|secure', 'shield'),
    (r'24\s*x\s*7|24/7|24 hour', 'clock'),
]


def amenity_icon(label):
    text = (label or '').lower()
    for pattern, icon in _AMENITY_ICONS:
        if re.search(pattern, text):
            return icon
    return 'check'


def parse_amenities(text):
    """Turn "Free WiFi, Parking" (or newline separated text) into
    [{'label': 'Free WiFi', 'icon': 'wifi'}, ...], skipping blanks and duplicates."""
    items, seen = [], set()
    for part in re.split(r'[,\n;]+', text or ''):
        label = part.strip()
        if label and label.lower() not in seen:
            seen.add(label.lower())
            items.append({'label': label, 'icon': amenity_icon(label)})
    return items


def format_duration(start, end):
    """2h 15m between two datetimes (never negative)."""
    minutes = max(0, int((end - start).total_seconds() // 60))
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return f'{hours}h {mins:02d}m'
    if hours:
        return f'{hours}h'
    return f'{mins}m'


def initials(name, length=2):
    """'Air India' -> 'AI', 'IndiGo' -> 'IN'. Used for the carrier logo badge."""
    words = re.findall(r'[A-Za-z0-9]+', name or '')
    if not words:
        return '?'
    if len(words) == 1:
        return words[0][:length].upper()
    return ''.join(w[0] for w in words[:length]).upper()


def parse_int(value, default=None, minimum=None):
    """int(value), or `default` when it is blank / not a number. Optionally clamped."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    if minimum is not None and number < minimum:
        return minimum
    return number


def parse_date(value):
    """'2026-11-20' -> date, or None when blank / malformed."""
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None
