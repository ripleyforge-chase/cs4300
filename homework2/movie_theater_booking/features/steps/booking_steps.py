from datetime import date
from behave import given, when, then
from bookings.models import Booking, Movie, Seat
from bookings.services import reserve_seat


@given("a movie with an available seat A1")
def movie_and_seat(context):
    context.movie = Movie.objects.create(title="The Last Orbit", description="A journey beyond Earth.", release_date=date(2026, 8, 14), duration=118)
    context.seat = Seat.objects.create(movie=context.movie, seat_number="A1")


@given("I am signed in")
def sign_in(context):
    context.api.force_authenticate(context.user)
    context.web.force_login(context.user)


@given("another moviegoer has booked seat A1")
def occupied(context):
    context.other_booking = reserve_seat(movie=context.movie, seat=context.seat, user=context.other)


@when("I request the movie API")
def browse(context):
    context.response = context.api.get("/api/movies/")


@then("the movie is listed as JSON")
def movie_json(context):
    assert context.response.status_code == 200
    assert context.response.headers["Content-Type"].startswith("application/json")
    assert context.response.json()[0]["title"] == context.movie.title


@then("the movie appears on the website")
def movie_html(context):
    assert context.movie.title in context.web.get("/").content.decode()


@when("I book seat A1 on the website")
def reserve_html(context):
    context.response = context.web.post(f"/movies/{context.movie.pk}/book/", {"seat": context.seat.pk}, follow=True)
    assert context.response.status_code == 200


@then("my ticket appears on the history page")
def ticket_html(context):
    html = context.web.get("/bookings/").content.decode()
    assert context.movie.title in html and "A1" in html


@then("the API contains my reservation")
def ticket_json(context):
    bookings = context.api.get("/api/bookings/").json()
    assert len(bookings) == 1
    assert bookings[0]["seat"] == context.seat.pk
    assert bookings[0]["user"] == context.user.pk


@then("seat A1 is unavailable")
def unavailable(context):
    assert context.api.get(f"/api/seats/{context.seat.pk}/").json()["booking_status"] is True


@when("I try to book seat A1 using the API")
def reserve_api(context):
    context.response = context.api.post("/api/bookings/", {"movie": context.movie.pk, "seat": context.seat.pk}, format="json")


@then("the API rejects the duplicate booking")
def duplicate(context):
    assert context.response.status_code == 400
    assert "just been booked" in str(context.response.json())


@then("exactly one booking exists")
def one_booking(context):
    assert Booking.objects.count() == 1


@when("I request my booking history")
def history(context):
    context.response = context.api.get("/api/bookings/")


@then("my API history is empty")
def empty_history(context):
    assert context.response.status_code == 200
    assert context.response.json() == []


@then("I cannot retrieve or cancel the other ticket")
def private_ticket(context):
    url = f"/api/bookings/{context.other_booking.pk}/"
    assert context.api.get(url).status_code == 404
    assert context.api.delete(url).status_code == 404


@when("I cancel my ticket using the API")
def cancel(context):
    booking = Booking.objects.get(user=context.user)
    assert context.api.delete(f"/api/bookings/{booking.pk}/").status_code == 204


@then("seat A1 is available")
def available(context):
    assert context.api.get(f"/api/seats/{context.seat.pk}/").json()["booking_status"] is False


@then("my website history is empty")
def empty_html(context):
    assert "Your next story is waiting." in context.web.get("/bookings/").content.decode()


@then("the API requires authentication")
def requires_login(context):
    assert context.response.status_code == 403


@then("no booking exists")
def no_booking(context):
    assert not Booking.objects.exists()
