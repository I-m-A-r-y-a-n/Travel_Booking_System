import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0005_booking_cancelled_at_booking_refund_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='group_ref',
            field=models.CharField(blank=True, db_index=True, max_length=32),
        ),
        migrations.AddField(
            model_name='booking',
            name='leg',
            field=models.CharField(blank=True, choices=[('outbound', 'Outbound'), ('return', 'Return')], max_length=10),
        ),
        migrations.CreateModel(
            name='Passenger',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('age', models.PositiveSmallIntegerField()),
                ('gender', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], max_length=1)),
                ('seat', models.CharField(blank=True, max_length=8)),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='travellers', to='bookings.booking')),
            ],
            options={'ordering': ['id']},
        ),
    ]
