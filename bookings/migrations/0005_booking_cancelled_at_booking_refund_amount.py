from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0004_booking_passengers'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='cancelled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='refund_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
