from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flights', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='flight',
            name='amenities',
            field=models.TextField(
                blank=True,
                default='Cabin baggage 7 kg, Check-in baggage 15 kg, In-flight meals available, Web check-in',
                help_text='Comma-separated list shown on the flight page, e.g. "Cabin baggage 7 kg, In-flight meals".',
            ),
        ),
    ]