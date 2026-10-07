from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Booking, Movie, Seat
from .services import reserve_seat


class BookingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("viewer", password="sample-password-123")
        self.other = get_user_model().objects.create_user("other", password="sample-password-123")
        self.movie = Movie.objects.create(title="The Last Orbit", description="A space adventure.", release_date=date(2026, 1, 1), duration=110)
        self.seat = Seat.objects.create(movie=self.movie, seat_number="A1")
        self.client = APIClient()

    def test_reserve_and_cancel_update_availability(self):
        self.assertFalse(self.seat.booking_status)
        booking = reserve_seat(movie=self.movie, seat=self.seat, user=self.user)
        self.assertTrue(Seat.objects.get(pk=self.seat.pk).booking_status)
        booking.delete()
        self.assertFalse(Seat.objects.get(pk=self.seat.pk).booking_status)

    def test_duplicate_reservation_is_rejected(self):
        reserve_seat(movie=self.movie, seat=self.seat, user=self.user)
        with self.assertRaisesMessage(ValidationError, "just been booked"):
            reserve_seat(movie=self.movie, seat=self.seat, user=self.other)
        self.assertEqual(Booking.objects.count(), 1)

    def test_public_movie_and_seat_json(self):
        response = self.client.get("/api/movies/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["title"], self.movie.title)
        response = self.client.get(f"/api/seats/?movie={self.movie.pk}")
        self.assertEqual(response.json()[0]["booking_status"], False)

    def test_booking_requires_login(self):
        response = self.client.post("/api/bookings/", {"movie": self.movie.pk, "seat": self.seat.pk})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Booking.objects.count(), 0)

    def test_api_booking_uses_authenticated_user(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/bookings/", {"movie": self.movie.pk, "seat": self.seat.pk, "user": self.other.pk})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["user"], self.user.pk)
        duplicate = self.client.post("/api/bookings/", {"movie": self.movie.pk, "seat": self.seat.pk})
        self.assertEqual(duplicate.status_code, 400)

    def test_history_and_cancellation_are_private(self):
        booking = reserve_seat(movie=self.movie, seat=self.seat, user=self.user)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get("/api/bookings/").json(), [])
        self.assertEqual(self.client.delete(f"/api/bookings/{booking.pk}/").status_code, 404)
        self.client.force_authenticate(self.user)
        self.assertEqual(len(self.client.get("/api/bookings/").json()), 1)
        self.assertEqual(self.client.delete(f"/api/bookings/{booking.pk}/").status_code, 204)
        self.assertFalse(Seat.objects.get(pk=self.seat.pk).booking_status)
