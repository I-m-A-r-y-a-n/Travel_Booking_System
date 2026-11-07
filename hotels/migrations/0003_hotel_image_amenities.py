from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotels', '0002_remove_hotel_price_per_night_room'),
    ]

    operations = [
        migrations.AddField(
            model_name='hotel',
            name='image_url',
            field=models.URLField(
                blank=True,
                help_text='Optional photo of the hotel (a full https:// link). A default photo is used when empty.',
                max_length=500,
            ),
        ),
        migrations.AddField(
            model_name='hotel',
            name='amenities',
            field=models.TextField(
                blank=True,
                default='Free WiFi, Air conditioning, 24x7 front desk, Room service, Parking',
                help_text='Comma-separated list shown on the hotel page, e.g. "Free WiFi, Swimming pool, Parking".',
            ),
        ),
    ]
