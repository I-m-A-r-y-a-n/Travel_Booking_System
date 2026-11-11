from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flights', '0002_flight_amenities'),
    ]

    operations = [
        migrations.AddField(
            model_name='flight',
            name='stops',
            field=models.PositiveSmallIntegerField(default=0, help_text='0 means non-stop.'),
        ),
        migrations.AddField(
            model_name='flight',
            name='via_city',
            field=models.CharField(blank=True, help_text='Where a one-stop flight changes planes.', max_length=100),
        ),
    ]
