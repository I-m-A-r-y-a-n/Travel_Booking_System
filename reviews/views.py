from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from bookings.models import Booking
from bookings.tickets import ticket_info
from buses.models import Bus
from flights.models import Flight
from hotels.models import Hotel

from .forms import ReviewForm
from .models import Review


def _stars(rating):
    """[True, True, True, False, False] for a 3 star rating, so templates can draw stars."""
    return [n < rating for n in range(5)]

ITEM_TYPES = {
    'hotel': (Hotel, 'booking__hotel'),
    'flight': (Flight, 'booking__flight'),
    'bus': (Bus, 'booking__bus'),
}


@login_required
def write_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    context = {'booking': booking, 'info': ticket_info(booking)}

    if booking.status != 'confirmed':
        context['not_allowed'] = True
        return render(request, 'reviews/write_review.html', context)

    if Review.objects.filter(booking=booking).exists():
        context['already_reviewed'] = True
        return render(request, 'reviews/write_review.html', context)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.booking = booking
            review.save()
            return redirect('reviews:my_reviews')
    else:
        form = ReviewForm()

    context['form'] = form
    return render(request, 'reviews/write_review.html', context)


@login_required
def my_reviews(request):
    reviews = list(
        Review.objects.filter(user=request.user)
        .select_related('booking__flight', 'booking__bus', 'booking__hotel', 'booking__room')
        .order_by('-created_at')
    )
    for review in reviews:
        review.star_list = _stars(review.rating)
        review.info = ticket_info(review.booking) if review.booking else None
    average = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else None
    return render(request, 'reviews/my_reviews.html', {
        'reviews': reviews, 'count': len(reviews), 'average': average,
    })


def item_reviews(request, item_type, item_id):
    if item_type not in ITEM_TYPES:
        raise Http404("Unknown item type")

    model, lookup = ITEM_TYPES[item_type]
    item = get_object_or_404(model, id=item_id)

    reviews = list(
        Review.objects.filter(**{lookup: item})
        .select_related('user')
        .order_by('-created_at')
    )
    for review in reviews:
        review.star_list = _stars(review.rating)
        name = (review.user.name or '').strip() or 'Traveler'
        review.display_name = name
        review.initial = name[:1].upper()

    count = len(reviews)
    average = round(sum(r.rating for r in reviews) / count, 1) if count else None
    breakdown = [
        {'stars': n, 'count': sum(1 for r in reviews if r.rating == n),
         'percent': round(100 * sum(1 for r in reviews if r.rating == n) / count) if count else 0}
        for n in (5, 4, 3, 2, 1)
    ]
    return render(request, 'reviews/item_reviews.html', {
        'item': item,
        'title': getattr(item, 'carrier', None) or getattr(item, 'name', str(item)),
        'item_type': item_type,
        'reviews': reviews,
        'count': count,
        'average': average,
        'average_stars': _stars(round(average) if average else 0),
        'breakdown': breakdown,
    })


@login_required
def edit_review(request, review_id):
    # user=request.user means people can only edit their own reviews.
    review = get_object_or_404(Review, id=review_id, user=request.user)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            return redirect('reviews:my_reviews')
    else:
        form = ReviewForm(instance=review)

    return render(request, 'reviews/edit_review.html', {
        'form': form, 'review': review,
        'booking': review.booking,
        'info': ticket_info(review.booking) if review.booking else None,
    })
@login_required
@require_POST
def delete_review(request, review_id):
    # user=request.user means people can only delete their own reviews.
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect('reviews:my_reviews')