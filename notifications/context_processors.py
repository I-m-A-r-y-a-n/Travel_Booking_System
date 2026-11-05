from .models import Notification


def unread_notifications(request):
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        count = Notification.objects.filter(user=user, is_read=False).count()
    else:
        count = 0
    return {'unread_notification_count': count}