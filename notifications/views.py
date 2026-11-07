from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .helpers import decorate, decorate_all
from .models import Notification

PANEL_SIZE = 8
PAGE_SIZE = 50


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


@login_required
def notification_list(request):
    notifications = decorate_all(
        Notification.objects.filter(user=request.user).order_by('-created_at')[:PAGE_SIZE], request.user
    )
    unread = sum(1 for n in notifications if not n.is_read)
    return render(request, 'notifications/list.html', {'notifications': notifications, 'unread': unread})


@login_required
def notification_panel(request):
    """The small dropdown under the bell (HTML fragment, loaded when it is opened)."""
    notifications = decorate_all(
        Notification.objects.filter(user=request.user).order_by('-created_at')[:PANEL_SIZE], request.user
    )
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, 'notifications/_panel.html', {'notifications': notifications, 'unread': unread})


@login_required
@require_POST
def open_notification(request, notification_id):
    """Mark one notification read and go to the booking it is about."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    target = decorate(notification, request.user).link  # '' when the booking is gone or not theirs
    return redirect(target or 'notifications:list')


@login_required
@require_POST
def mark_read(request, notification_id):
    # user=request.user means people can only touch their own notifications.
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications:list')


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if _is_ajax(request):
        return JsonResponse({'ok': True})
    return redirect('notifications:list')
