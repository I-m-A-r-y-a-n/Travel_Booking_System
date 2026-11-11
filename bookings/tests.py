"""Tests for the booking rules. Run them with:  python manage.py test bookings"""
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from buses.models import Bus
from flights.models import Flight
from hotels.models import Hotel, Room
from payments.models import Payment

from . import rules
from .models import Booking, Passenger
from .seats import all_labels, seat_layout
from .utils import seats_available


def make_user(n):
    return User.objects.create_user(
        username=f'user{n}@example.com', email=f'user{n}@example.com', password='pass12345',
        name=f'User {n}', mobile_number=f'90000000{n:02d}',
    )


def make_flight(hours_ahead=72, seats=10, number='AI100', price=1000):
    departure = timezone.now() + timedelta(hours=hours_ahead)
    return Flight.objects.create(
        airline_name='Air Test', flight_number=number, departure_city='Bangalore',
        destination_city='Delhi', departure_time=departure,
        arrival_time=departure + timedelta(hours=3), total_seats=seats, price=Decimal(price),
    )


def details(n, **extra):
    """The form fields for n passengers (names use letters only, as the form requires)."""
    data = {'passengers': n}
    for i in range(1, n + 1):
        data.update({f'name_{i}': f'Test {chr(64 + i)}', f'age_{i}': 20 + i, f'gender_{i}': 'F'})
    data.update(extra)
    return data


def make_bus(hours_ahead=72, seats=8, number='KA100', bus_type='AC_SEATER'):
    departure = timezone.now() + timedelta(hours=hours_ahead)
    return Bus.objects.create(
        operator_name='Bus Test', bus_number=number, starting_location='Chennai', destination='Bangalore',
        departure_time=departure, arrival_time=departure + timedelta(hours=7), total_seats=seats,
        price=Decimal('800'), bus_type=bus_type,
    )


def make_return_flight(outbound, hours_after=48, number='AI900', seats=10):
    departure = outbound.arrival_time + timedelta(hours=hours_after)
    return Flight.objects.create(
        airline_name='Air Test', flight_number=number, departure_city=outbound.destination_city,
        destination_city=outbound.departure_city, departure_time=departure,
        arrival_time=departure + timedelta(hours=3), total_seats=seats, price=Decimal('1500'),
    )


def make_room(total_rooms=1, capacity=2):
    hotel = Hotel.objects.create(name='Test Inn', location='Goa')
    return Room.objects.create(
        hotel=hotel, room_type='STANDARD', price_per_night=Decimal('2000'),
        capacity=capacity, total_rooms=total_rooms, available_rooms=total_rooms,
    )


def make_booking(user, flight, status='confirmed', passengers=1):
    return Booking.objects.create(
        user=user, booking_type='flight', flight=flight, passengers=passengers,
        total_price=flight.price * passengers, status=status,
    )


class SeatTests(TestCase):
    def setUp(self):
        self.a, self.b = make_user(1), make_user(2)
        self.flight = make_flight(seats=10)

    def book(self, user, passengers):
        self.client.force_login(user)
        return self.client.post(reverse('book_flight', args=[self.flight.id]), details(passengers))

    def test_seats_fill_up_and_sold_out(self):
        self.assertEqual(self.book(self.a, 6).status_code, 302)
        self.assertEqual(seats_available(self.flight, 'flight'), 4)
        self.assertEqual(self.book(self.b, 4).status_code, 302)
        self.assertEqual(seats_available(self.flight, 'flight'), 0)
        # nothing left for a third person: the page re-renders instead of creating a booking
        self.assertEqual(self.book(make_user(3), 1).status_code, 200)
        self.assertEqual(Booking.objects.count(), 2)

    def test_unpaid_hold_expires_and_frees_seats(self):
        booking = make_booking(self.a, self.flight, status='pending', passengers=10)
        self.assertEqual(seats_available(self.flight, 'flight'), 0)
        Booking.objects.filter(pk=booking.pk).update(
            booking_date=timezone.now() - timedelta(minutes=rules.HOLD_MINUTES + 1))
        self.assertEqual(seats_available(self.flight, 'flight'), 10)

    def test_cancelled_booking_frees_seats(self):
        make_booking(self.a, self.flight, status='cancelled', passengers=10)
        self.assertEqual(seats_available(self.flight, 'flight'), 10)

    def test_double_submit_reuses_the_same_booking(self):
        self.book(self.a, 2)
        self.book(self.a, 3)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(Booking.objects.get().passengers, 3)

    def test_passenger_limit(self):
        big = make_flight(seats=100, number='AI200')
        self.client.force_login(self.a)
        response = self.client.post(reverse('book_flight', args=[big.id]), {'passengers': 10})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Booking.objects.count(), 0)


class DateRuleTests(TestCase):
    def setUp(self):
        self.user = make_user(1)
        self.client.force_login(self.user)

    def test_cannot_book_a_departed_flight(self):
        flight = make_flight(hours_ahead=-3, number='AI300')
        response = self.client.post(reverse('book_flight', args=[flight.id]), {'passengers': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Booking.objects.count(), 0)

    def test_booking_closes_before_departure(self):
        flight = make_flight(hours_ahead=1, number='AI301')
        self.client.post(reverse('book_flight', args=[flight.id]), {'passengers': 1})
        self.assertEqual(Booking.objects.count(), 0)

    def test_search_rejects_past_dates(self):
        yesterday = (timezone.localdate() - timedelta(days=1)).isoformat()
        response = self.client.get(reverse('flight_search'), {
            'departure_city': 'Bangalore', 'destination_city': 'Delhi', 'date': yesterday, 'passengers': 1})
        self.assertFalse(response.context['searched'])
        self.assertIn('date', response.context['form'].errors)

    def test_departed_flights_are_hidden_from_results(self):
        flight = make_flight(hours_ahead=-2, number='AI302')
        today = timezone.localdate().isoformat()
        response = self.client.get(reverse('flight_search'), {
            'departure_city': 'Bangalore', 'destination_city': 'Delhi', 'date': today, 'passengers': 1})
        self.assertNotIn(flight, response.context['items'])


class HotelTests(TestCase):
    def setUp(self):
        self.a, self.b = make_user(1), make_user(2)
        self.room = make_room(total_rooms=1)
        self.check_in = timezone.localdate() + timedelta(days=10)

    def book(self, user, nights=2, guests=2):
        self.client.force_login(user)
        return self.client.post(reverse('hotels:book_room', args=[self.room.id]), {
            'check_in': self.check_in.isoformat(),
            'check_out': (self.check_in + timedelta(days=nights)).isoformat(),
            'guests': guests,
        })

    def test_last_room_goes_to_the_first_person(self):
        self.assertEqual(self.book(self.a).status_code, 302)
        self.assertEqual(self.book(self.b).status_code, 200)  # "No rooms available"
        self.assertEqual(Booking.objects.count(), 1)

    def test_overlap_blocked_but_other_dates_fine(self):
        self.book(self.a, nights=3)
        self.check_in += timedelta(days=3)  # starts the day the first stay ends
        self.assertEqual(self.book(self.b).status_code, 302)

    def test_stay_limits(self):
        self.book(self.a, nights=rules.MAX_STAY_NIGHTS + 1)
        self.assertEqual(Booking.objects.count(), 0)

    def test_too_many_guests(self):
        self.book(self.a, guests=5)
        self.assertEqual(Booking.objects.count(), 0)


class PaymentTests(TestCase):
    def setUp(self):
        self.user = make_user(1)
        self.client.force_login(self.user)
        self.flight = make_flight()
        self.booking = make_booking(self.user, self.flight, status='pending', passengers=2)
        self.url = reverse('payments:process_payment', args=[self.booking.id])

    def test_failed_payment_keeps_the_hold_and_retry_works(self):
        with mock.patch('payments.views.random.random', return_value=0.99):
            self.client.post(self.url, {'method': 'UPI'})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'pending')
        self.assertEqual(Payment.objects.get().status, 'FAILED')
        with mock.patch('payments.views.random.random', return_value=0.0):
            self.client.post(self.url, {'method': 'UPI'})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'confirmed')

    def test_expired_booking_cannot_be_paid(self):
        Booking.objects.filter(pk=self.booking.pk).update(
            booking_date=timezone.now() - timedelta(minutes=rules.HOLD_MINUTES + 1))
        self.client.post(self.url, {'method': 'UPI'})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'cancelled')
        self.assertEqual(Payment.objects.count(), 0)

    def test_confirmed_booking_cannot_be_paid_twice(self):
        with mock.patch('payments.views.random.random', return_value=0.0):
            self.client.post(self.url, {'method': 'CARD'})
            self.client.post(self.url, {'method': 'CARD'})
        self.assertEqual(Payment.objects.count(), 1)


class CancellationTests(TestCase):
    def setUp(self):
        self.user = make_user(1)
        self.client.force_login(self.user)

    def test_refund_tiers(self):
        for hours, percent in ((100, 90), (50, 75), (10, 50)):
            flight = make_flight(hours_ahead=hours, number=f'AI{hours}', price=1000)
            result = rules.refund_for(make_booking(self.user, flight))
            self.assertTrue(result['allowed'])
            self.assertEqual(result['percent'], percent)
            self.assertEqual(result['amount'], Decimal(10 * percent))

    def test_cannot_cancel_close_to_or_after_departure(self):
        for hours in (3, -1):
            flight = make_flight(hours_ahead=hours, number=f'AX{hours + 5}')
            self.assertFalse(rules.refund_for(make_booking(self.user, flight))['allowed'])

    def test_cancel_records_refund(self):
        booking = make_booking(self.user, make_flight(hours_ahead=100), passengers=2)
        self.client.post(reverse('cancel_booking', args=[booking.id]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
        self.assertEqual(booking.refund_amount, Decimal('1800.00'))
        self.assertIsNotNone(booking.cancelled_at)

    def test_unpaid_booking_cancels_with_no_refund(self):
        booking = make_booking(self.user, make_flight(hours_ahead=1, number='AI900'), status='pending')
        self.client.post(reverse('cancel_booking', args=[booking.id]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
        self.assertEqual(booking.refund_amount, 0)

    def test_departed_trip_cannot_be_cancelled(self):
        booking = make_booking(self.user, make_flight(hours_ahead=-5, number='AI901'))
        self.client.post(reverse('cancel_booking', args=[booking.id]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'confirmed')


class ReviewRuleTests(TestCase):
    def setUp(self):
        self.user = make_user(1)
        self.client.force_login(self.user)

    def test_cannot_review_before_the_trip_is_over(self):
        booking = make_booking(self.user, make_flight(hours_ahead=48))
        response = self.client.get(reverse('reviews:write_review', args=[booking.id]))
        self.assertTrue(response.context['not_allowed'])

    def test_can_review_after_the_trip(self):
        booking = make_booking(self.user, make_flight(hours_ahead=-48, number='AI777'))
        response = self.client.get(reverse('reviews:write_review', args=[booking.id]))
        self.assertNotIn('not_allowed', response.context)


class PassengerDetailTests(TestCase):
    def setUp(self):
        self.user = make_user(1)
        self.flight = make_flight(seats=10, number='AI400')
        self.client.force_login(self.user)
        self.url = reverse('book_flight', args=[self.flight.id])

    def test_details_are_saved_with_the_booking(self):
        self.assertEqual(self.client.post(self.url, details(2)).status_code, 302)
        booking = Booking.objects.get()
        self.assertEqual(booking.travellers.count(), 2)
        first = booking.travellers.first()
        self.assertEqual((first.name, first.age, first.gender), ('Test A', 21, 'F'))

    def test_missing_or_bad_details_block_the_booking(self):
        self.assertEqual(self.client.post(self.url, {'passengers': 2}).status_code, 200)
        bad = details(1, name_1='R2D2', age_1='200', gender_1='X')
        response = self.client.post(self.url, bad)
        self.assertEqual(response.status_code, 200)
        errors = response.context['rows'][0]['errors']
        self.assertEqual(set(errors), {'name', 'age', 'gender'})
        self.assertEqual(Booking.objects.count(), 0)

    def test_rebooking_replaces_the_travellers(self):
        self.client.post(self.url, details(2))
        self.client.post(self.url, details(1))
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(Passenger.objects.count(), 1)

    def test_review_page_prefills_the_first_name(self):
        response = self.client.get(self.url, {'passengers': 2})
        self.assertEqual(response.context['rows'][0]['name'], 'User 1')
        self.assertEqual(len(response.context['rows']), 2)


class SeatSelectionTests(TestCase):
    def setUp(self):
        self.a, self.b = make_user(1), make_user(2)
        self.flight = make_flight(seats=10, number='AI500')

    def book(self, user, seats, count=None, flight=None):
        flight = flight or self.flight
        self.client.force_login(user)
        count = count or len(seats)
        return self.client.post(reverse('book_flight', args=[flight.id]), details(count, seats_0=seats))

    def test_chosen_seats_are_saved_on_each_passenger(self):
        self.assertEqual(self.book(self.a, ['2A', '2B']).status_code, 302)
        self.assertEqual(list(Passenger.objects.values_list('seat', flat=True)), ['2A', '2B'])

    def test_flight_seats_are_optional(self):
        self.assertEqual(self.book(self.a, [], count=2).status_code, 302)
        self.assertEqual(Passenger.objects.exclude(seat='').count(), 0)

    def test_a_taken_seat_cannot_be_booked_again(self):
        self.book(self.a, ['1A'])
        response = self.book(self.b, ['1A'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertIn('1A', response.context['legs'][0].taken)

    def test_cancelled_or_lapsed_bookings_release_their_seats(self):
        self.book(self.a, ['1A'])
        Booking.objects.update(status='cancelled')
        self.assertEqual(self.book(self.b, ['1A']).status_code, 302)

    def test_same_user_can_repost_their_own_held_seats(self):
        self.book(self.a, ['1A', '1B'])
        self.assertEqual(self.book(self.a, ['1A', '1B']).status_code, 302)
        self.assertEqual(Passenger.objects.count(), 2)

    def test_wrong_number_of_seats_or_invalid_seat(self):
        self.assertEqual(self.book(self.a, ['1A'], count=2).status_code, 200)
        self.assertEqual(self.book(self.a, ['99Z']).status_code, 200)
        self.assertEqual(Booking.objects.count(), 0)

    def test_bus_seats_are_required(self):
        bus = make_bus()
        self.client.force_login(self.a)
        url = reverse('book_bus', args=[bus.id])
        self.assertEqual(self.client.post(url, details(2)).status_code, 200)
        self.assertEqual(self.client.post(url, details(2, seats_0=['1A', '1B'])).status_code, 302)

    def test_seat_maps_match_the_trip(self):
        self.assertEqual(len(all_labels(self.flight, 'flight')), 10)
        seater = make_bus(seats=9, number='KA101')
        self.assertEqual(len(all_labels(seater, 'bus')), 9)
        sleeper = make_bus(seats=9, number='KA102', bus_type='AC_SLEEPER')
        labels = all_labels(sleeper, 'bus')
        self.assertEqual(len(labels), 9)
        self.assertEqual(sum(l.startswith('L') for l in labels), 5)
        layout = seat_layout(sleeper, 'bus', taken={'L1'})
        self.assertEqual([d['name'] for d in layout['decks']], ['Lower deck', 'Upper deck'])
        self.assertEqual(layout['free'], 8)


class RoundTripTests(TestCase):
    def setUp(self):
        self.user = make_user(1)
        self.out = make_flight(seats=10, number='AI600')
        self.back = make_return_flight(self.out)
        self.client.force_login(self.user)
        self.url = reverse('book_flight', args=[self.out.id])

    def post(self, **extra):
        return self.client.post(self.url, details(2, **{'return': self.back.id}, **extra))

    def test_both_legs_are_held_together(self):
        self.assertEqual(self.post(seats_0=['1A', '1B'], seats_1=['2A', '2B']).status_code, 302)
        bookings = list(Booking.objects.order_by('id'))
        self.assertEqual([b.leg for b in bookings], ['outbound', 'return'])
        self.assertEqual(bookings[0].group_ref, bookings[1].group_ref)
        self.assertNotEqual(bookings[0].group_ref, '')
        self.assertEqual(bookings[1].total_price, Decimal('3000'))
        self.assertEqual(seats_available(self.back, 'flight'), 8)

    def test_return_must_leave_after_arrival_and_run_the_other_way(self):
        early = make_return_flight(self.out, hours_after=-5, number='AI901')
        response = self.client.post(self.url, details(1, **{'return': early.id}))
        self.assertEqual(response.status_code, 200)
        same_way = make_flight(hours_ahead=200, number='AI902')
        response = self.client.post(self.url, details(1, **{'return': same_way.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Booking.objects.count(), 0)

    def test_nothing_is_held_when_the_return_is_full(self):
        make_booking(make_user(2), self.back, passengers=10)
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(Booking.objects.filter(user=self.user).count(), 0)

    def test_one_payment_confirms_both_legs(self):
        self.post()
        first = Booking.objects.order_by('id').first()
        with mock.patch('payments.views.random.random', return_value=0.0):
            self.client.post(reverse('payments:process_payment', args=[first.id]), {'method': 'UPI'})
        self.assertEqual(set(Booking.objects.values_list('status', flat=True)), {'confirmed'})
        self.assertEqual(Payment.objects.filter(status='SUCCESS').count(), 2)

    def test_failed_payment_keeps_both_legs_on_hold(self):
        self.post()
        first = Booking.objects.order_by('id').first()
        with mock.patch('payments.views.random.random', return_value=0.99):
            self.client.post(reverse('payments:process_payment', args=[first.id]), {'method': 'UPI'})
        self.assertEqual(set(Booking.objects.values_list('status', flat=True)), {'pending'})

    def test_payment_page_shows_the_combined_total(self):
        self.post()
        first = Booking.objects.order_by('id').first()
        response = self.client.get(reverse('payments:choose_payment_method', args=[first.id]))
        self.assertEqual(response.context['amount'], Decimal('5000'))
        self.assertEqual(len(response.context['legs']), 2)


class SearchFilterTests(TestCase):
    def setUp(self):
        self.user = make_user(1)
        self.client.force_login(self.user)
        self.cheap = make_flight(hours_ahead=72, number='AI700', price=2000)
        self.pricey = make_flight(hours_ahead=96, number='AI701', price=9000)
        self.stop = make_flight(hours_ahead=72, number='AI702', price=1500)
        self.stop.stops, self.stop.via_city = 1, 'Hyderabad'
        self.stop.save()
        self.day = self.cheap.departure_time.date().isoformat()

    def search(self, **extra):
        params = {'departure_city': 'Bangalore', 'destination_city': 'Delhi', 'date': self.day, 'passengers': 1}
        params.update(extra)
        return self.client.get(reverse('flight_search'), params)

    def test_non_stop_filter(self):
        self.assertIn(self.stop, self.search().context['items'])
        items = self.search(nonstop='1').context['items']
        self.assertNotIn(self.stop, items)
        self.assertIn(self.cheap, items)

    def test_price_filter_ignores_the_slider_maximum(self):
        everything = self.search(max_price='99999').context['items']
        self.assertIn(self.cheap, everything)
        self.assertEqual(self.search(max_price='1800').context['items'], [self.stop])

    def test_departure_time_filter(self):
        hour = timezone.localtime(self.cheap.departure_time).hour
        buckets = {'early': range(0, 6), 'morning': range(6, 12), 'afternoon': range(12, 18), 'evening': range(18, 24)}
        mine = next(k for k, hours in buckets.items() if hour in hours)
        other = next(k for k in buckets if k != mine)
        self.assertIn(self.cheap, self.search(dep=mine).context['items'])
        self.assertNotIn(self.cheap, self.search(dep=other).context['items'])

    def test_stop_label_and_sorting(self):
        self.assertEqual(self.stop.tag, '1 stop via Hyderabad')
        prices = [f.price for f in self.search(sort='price').context['items']]
        self.assertEqual(prices, sorted(prices))

    def test_round_trip_second_step_lists_only_later_return_flights(self):
        back = make_return_flight(self.cheap, number='AI800')
        too_early = make_return_flight(self.cheap, hours_after=-4, number='AI801')
        response = self.search(trip='round', outbound=self.cheap.id,
                               return_date=back.departure_time.date().isoformat())
        self.assertEqual(response.context['step'], 2)
        self.assertEqual(response.context['items'], [back])
        self.assertNotIn(too_early, response.context['items'])
        self.assertEqual(response.context['items'][0].pair_total, self.cheap.price + back.price)

    def test_round_trip_needs_a_return_date_not_before_departure(self):
        response = self.search(trip='round')
        self.assertFalse(response.context['searched'])
        earlier = (self.cheap.departure_time - timedelta(days=1)).date().isoformat()
        self.assertFalse(self.search(trip='round', return_date=earlier).context['searched'])

    def test_bus_type_filter(self):
        seater = make_bus(number='KA200')
        sleeper = make_bus(number='KA201', bus_type='AC_SLEEPER')
        day = seater.departure_time.date().isoformat()
        params = {'starting_location': 'Chennai', 'destination': 'Bangalore', 'date': day, 'passengers': 1}
        items = self.client.get(reverse('bus_search'), dict(params, bus_type='AC_SLEEPER')).context['items']
        self.assertEqual(items, [sleeper])
