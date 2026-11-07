from django.db.models import Avg

from .models import Review

# Same lookups as ITEM_TYPES in reviews/views.py.
LOOKUPS = {
    'hotel': 'booking__hotel',
    'flight': 'booking__flight',
    'bus': 'booking__bus',
}


def review_summary(item_type, item, limit=3):
    """Average rating, count and the latest few reviews for a hotel/flight/bus."""
    reviews = (
        Review.objects.filter(**{LOOKUPS[item_type]: item})
        .select_related('user')
        .order_by('-created_at')
    )
    average = reviews.aggregate(avg=Avg('rating'))['avg']
    return {
        'count': reviews.count(),
        'average': round(average, 1) if average is not None else None,
        'latest': list(reviews[:limit]),
    }