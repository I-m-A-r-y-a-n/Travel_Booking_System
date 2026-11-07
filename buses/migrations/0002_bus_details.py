from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bus',
            name='bus_type',
            field=models.CharField(
                choices=[
                    ('AC_SEATER', 'AC Seater'),
                    ('NONAC_SEATER', 'Non-AC Seater'),
                    ('AC_SLEEPER', 'AC Sleeper'),
                    ('NONAC_SLEEPER', 'Non-AC Sleeper'),
                    ('VOLVO', 'Volvo Multi-Axle'),
                ],
                default='AC_SEATER',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='bus',
            name='amenities',
            field=models.TextField(
                blank=True,
                default='Air conditioning, Charging point, Reading light, Water bottle, Live bus tracking',
                help_text='Comma-separated list shown on the bus page, e.g. "Air conditioning, Charging point".',
            ),
        ),
        migrations.AddField(
            model_name='bus',
            name='image_url',
            field=models.URLField(
                blank=True,
                help_text='Optional photo of the bus (a full https:// link).',
                max_length=500,
            ),
        ),
    ]
