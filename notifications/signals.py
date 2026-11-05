from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from bookings.models import Booking
from payments.models import Payment

from .models import Notification


def _notify(user, notification_type, message):
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        message=message,
    )


def _remember_old_status(sender, instance):
    """Save the status currently in the database, so we can tell what changed."""
    if instance.pk:
        instance._old_status = (
            sender.objects.filter(pk=instance.pk)
            .values_list('status', flat=True)
            .first()
        )
    else:
        instance._old_status = None


@receiver(pre_save, sender=Booking)
def booking_pre_save(sender, instance, **kwargs):
    _remember_old_status(sender, instance)


@receiver(post_save, sender=Booking)
def booking_post_save(sender, instance, created, **kwargs):
    old = getattr(instance, '_old_status', None)

    if created:
        _notify(
            instance.user,
            'booking_confirmation',
            f"Booking #{instance.id} ({instance.get_booking_type_display()}) has been placed. "
            f"Complete the payment to confirm it.",
        )
    elif instance.status == 'confirmed' and old != 'confirmed':
        _notify(
            instance.user,
            'booking_confirmation',
            f"Booking #{instance.id} is confirmed. Have a great trip!",
        )
    elif instance.status == 'cancelled' and old != 'cancelled':
        _notify(
            instance.user,
            'cancellation',
            f"Booking #{instance.id} has been cancelled.",
        )


@receiver(pre_save, sender=Payment)
def payment_pre_save(sender, instance, **kwargs):
    _remember_old_status(sender, instance)


@receiver(post_save, sender=Payment)
def payment_post_save(sender, instance, created, **kwargs):
    old = getattr(instance, '_old_status', None)

    if instance.status in ('SUCCESS', 'FAILED') and (created or old != instance.status):
        result = 'was successful' if instance.status == 'SUCCESS' else 'failed'
        _notify(
            instance.booking.user,
            'payment_confirmation',
            f"Your payment of Rs. {instance.amount} for booking #{instance.booking_id} {result}.",
        )