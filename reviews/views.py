from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from bookings.models import Booking
from buses.models import Bus
from flights.models import Flight
from hotels.models import Hotel

from .forms import ReviewForm
from .models import Review

ITEM_TYPES = {
    'hotel': (Hotel, 'booking__hotel'),
    'flight': (Flight, 'booking__flight'),
    'bus': (Bus, 'booking__bus'),
}


@login_required
def write_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    context = {'booking': booking}

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
    reviews = (
        Review.objects.filter(user=request.user)
        .select_related('booking')
        .order_by('-created_at')
    )
    return render(request, 'reviews/my_reviews.html', {'reviews': reviews})


def item_reviews(request, item_type, item_id):
    if item_type not in ITEM_TYPES:
        raise Http404("Unknown item type")

    model, lookup = ITEM_TYPES[item_type]
    item = get_object_or_404(model, id=item_id)

    reviews = (
        Review.objects.filter(**{lookup: item})
        .select_related('user')
        .order_by('-created_at')
    )
    average = reviews.aggregate(avg=Avg('rating'))['avg']
    if average is not None:
        average = round(average, 1)

    return render(request, 'reviews/item_reviews.html', {
        'item': item,
        'reviews': reviews,
        'average': average,
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

    return render(request, 'reviews/edit_review.html', {'form': form, 'review': review})
@login_required
@require_POST
def delete_review(request, review_id):
    # user=request.user means people can only delete their own reviews.
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect('reviews:my_reviews')