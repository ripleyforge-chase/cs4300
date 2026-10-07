from datetime import date
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.urls import reverse

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
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
        self.web = Client()

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


    def test_movie_crud_requires_staff(self):
        payload = {"title": "New film", "description": "A new story", "release_date": "2026-09-01", "duration": 95}
        self.assertEqual(self.client.post("/api/movies/", payload).status_code, 403)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post("/api/movies/", payload).status_code, 403)
        self.user.is_staff = True
        self.user.save()
        created = self.client.post("/api/movies/", payload)
        self.assertEqual(created.status_code, 201)
        url = f"/api/movies/{created.json()['id']}/"
        self.assertEqual(self.client.get(url).json()["duration"], 95)
        self.assertEqual(self.client.patch(url, {"title": "Revised film"}).status_code, 200)
        self.assertEqual(self.client.get(url).json()["title"], "Revised film")
        self.assertEqual(self.client.put(url, payload).status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_invalid_movie_fields(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)
        for duration in (0, -3, "not a number"):
            response = self.client.post("/api/movies/", {"title": "X", "description": "Y", "release_date": "2026-01-01", "duration": duration})
            self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.post("/api/movies/", {}).status_code, 400)

    def test_seat_booking_action(self):
        url = f"/api/seats/{self.seat.pk}/book/"
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_authenticate(self.user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["seat_number"], "A1")
        self.assertTrue(self.client.get(f"/api/seats/{self.seat.pk}/").json()["booking_status"])
        self.assertEqual(self.client.post(url).status_code, 400)

    def test_seats_cannot_be_marked_booked_directly(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.patch(f"/api/seats/{self.seat.pk}/", {"booking_status": True}).status_code, 405)
        self.assertFalse(Seat.objects.get(pk=self.seat.pk).booking_status)

    def test_invalid_seat_filter_returns_validation_error(self):
        for value in ("abc", "0", "-1", ""):
            self.assertEqual(self.client.get("/api/seats/", {"movie": value}).status_code, 400)
        self.assertEqual(self.client.get("/api/seats/?movie=99999").json(), [])

    def test_invalid_booking_payloads(self):
        self.client.force_authenticate(self.user)
        for payload in ({}, {"movie": self.movie.pk, "seat": 99999}, {"movie": 99999, "seat": self.seat.pk}):
            self.assertEqual(self.client.post("/api/bookings/", payload).status_code, 400)
        self.assertEqual(Booking.objects.count(), 0)

    def test_wrong_movie_cannot_use_seat(self):
        other_movie = Movie.objects.create(title="Other", description="Other", release_date=date(2026, 1, 1), duration=90)
        with self.assertRaises(ValidationError):
            reserve_seat(movie=other_movie, seat=self.seat, user=self.user)
        with self.assertRaises(ValidationError):
            Booking(movie=other_movie, seat=self.seat, user=self.user).clean()
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post("/api/bookings/", {"movie": other_movie.pk, "seat": self.seat.pk}).status_code, 400)

    def test_different_movies_can_book_same_seat_number(self):
        other_movie = Movie.objects.create(title="Other", description="Other", release_date=date(2026, 1, 1), duration=90)
        other_seat = Seat.objects.create(movie=other_movie, seat_number="A1")
        reserve_seat(movie=self.movie, seat=self.seat, user=self.user)
        reserve_seat(movie=other_movie, seat=other_seat, user=self.other)
        self.assertEqual(Booking.objects.count(), 2)
        self.assertEqual(len(self.client.get(f"/api/seats/?movie={self.movie.pk}").json()), 1)

    def test_database_rejects_duplicate_seat_and_booking(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Seat.objects.create(movie=self.movie, seat_number="A1")
        reserve_seat(movie=self.movie, seat=self.seat, user=self.user)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Booking.objects.create(movie=self.movie, seat=self.seat, user=self.other)

    def test_unrelated_integrity_errors_are_not_disguised(self):
        with patch("bookings.services.Booking.objects.create", side_effect=IntegrityError("other failure")):
            with self.assertRaises(IntegrityError):
                reserve_seat(movie=self.movie, seat=self.seat, user=self.user)

    def test_model_labels_and_validation(self):
        booking = reserve_seat(movie=self.movie, seat=self.seat, user=self.user)
        booking.clean()
        self.assertEqual(str(self.movie), "The Last Orbit")
        self.assertIn("A1", str(self.seat))
        self.assertIn("viewer", str(booking))
        self.movie.duration = 0
        with self.assertRaises(ValidationError):
            self.movie.full_clean()
        self.seat.seat_number = "wrong"
        with self.assertRaises(ValidationError):
            self.seat.full_clean()

    def test_booking_cannot_be_reassigned(self):
        booking = reserve_seat(movie=self.movie, seat=self.seat, user=self.user)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.patch(f"/api/bookings/{booking.pk}/", {"user": self.other.pk}).status_code, 405)
        self.assertEqual(self.client.get(f"/api/bookings/{booking.pk}/").json()["movie_title"], self.movie.title)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/bookings/{booking.pk}/").status_code, 404)

    def test_html_list_search_and_empty_state(self):
        self.assertContains(self.web.get("/"), "The Last Orbit")
        self.assertContains(self.web.get("/?q=space"), "The Last Orbit")
        self.assertContains(self.web.get("/?q=unmatched"), "No films found")
        self.assertContains(self.web.get("/"), "1 seats left")

    def test_html_login_required(self):
        for url in (reverse("book_seat", args=[self.movie.pk]), reverse("booking_history")):
            response = self.web.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/accounts/login/?next=", response.url)

    def test_html_booking_matches_api_history(self):
        self.web.force_login(self.user)
        url = reverse("book_seat", args=[self.movie.pk])
        self.assertContains(self.web.get(url), "Choose your seat.")
        response = self.web.post(url, {"seat": self.seat.pk}, follow=True)
        self.assertContains(response, "booked!")
        self.assertContains(response, "A1")
        self.assertEqual(self.web.get("/api/bookings/").json()[0]["seat"], self.seat.pk)
        self.assertContains(self.web.get(url), "fully booked")

    def test_html_duplicate_or_invalid_seat_shows_error(self):
        self.web.force_login(self.user)
        url = reverse("book_seat", args=[self.movie.pk])
        reserve_seat(movie=self.movie, seat=self.seat, user=self.other)
        for payload in ({"seat": self.seat.pk}, {"seat": "invalid"}, {"seat": 99999}, {}):
            response = self.web.post(url, payload)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
        self.assertEqual(Booking.objects.count(), 1)

    def test_html_race_displays_recoverable_error(self):
        self.web.force_login(self.user)
        with patch("bookings.views.reserve_seat", side_effect=ValidationError("That seat has just been booked.")):
            response = self.web.post(reverse("book_seat", args=[self.movie.pk]), {"seat": self.seat.pk})
        self.assertContains(response, "That seat has just been booked.")

    def test_html_cancel_is_private_and_post_only(self):
        booking = reserve_seat(movie=self.movie, seat=self.seat, user=self.user)
        url = reverse("cancel_booking", args=[booking.pk])
        self.web.force_login(self.other)
        self.assertEqual(self.web.post(url).status_code, 404)
        self.web.force_login(self.user)
        self.assertEqual(self.web.get(url).status_code, 405)
        self.assertContains(self.web.post(url, follow=True), "The seat is available again.")
        self.assertFalse(Booking.objects.exists())
        self.assertContains(self.web.get(reverse("booking_history")), "Your next story is waiting.")

    def test_signup_login_logout(self):
        self.assertContains(self.web.get(reverse("signup")), "No email needed.")
        invalid = self.web.post(reverse("signup"), {"username": "newviewer", "password1": "123", "password2": "different"})
        self.assertTrue(invalid.context["form"].errors)
        response = self.web.post(reverse("signup"), {"username": "newviewer", "password1": "screening-pass-2026", "password2": "screening-pass-2026"})
        self.assertRedirects(response, "/")
        self.assertRedirects(self.web.get(reverse("signup")), "/")
        self.assertRedirects(self.web.post(reverse("logout")), "/")
        self.assertContains(self.web.get(reverse("login")), "Welcome back.")
        self.assertRedirects(self.web.post(reverse("login"), {"username": "newviewer", "password": "screening-pass-2026"}), "/")

    def test_csrf_required_for_html_and_session_api(self):
        protected = APIClient(enforce_csrf_checks=True)
        protected.force_login(self.user)
        self.assertEqual(protected.post(reverse("book_seat", args=[self.movie.pk]), {"seat": self.seat.pk}).status_code, 403)
        self.assertEqual(protected.post("/api/bookings/", {"movie": self.movie.pk, "seat": self.seat.pk}).status_code, 403)
        self.assertFalse(Booking.objects.exists())

    def test_missing_movie_and_readiness(self):
        self.web.force_login(self.user)
        self.assertEqual(self.web.get("/movies/99999/book/").status_code, 404)
        self.assertEqual(self.web.get("/health/").json(), {"status": "ok"})

    def test_seed_is_repeatable_and_preserves_reservations(self):
        output = StringIO()
        call_command("seed_demo", stdout=output)
        movie = Movie.objects.get(title="Coastline")
        seat = movie.seats.first()
        booking = reserve_seat(movie=movie, seat=seat, user=self.user)
        call_command("seed_demo", stdout=output)
        self.assertEqual(Movie.objects.count(), 3)
        self.assertEqual(Seat.objects.count(), 96)
        self.assertTrue(Booking.objects.filter(pk=booking.pk).exists())
        self.assertContains(self.web.get("/"), "Coastline")
        self.assertContains(self.web.get("/"), "Midnight Express")
