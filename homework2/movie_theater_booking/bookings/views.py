from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import BookingForm, SignUpForm
from .models import Booking, Movie
from .services import reserve_seat


def movie_list(request):
    movies = Movie.objects.annotate(available_seats=Count("seats", filter=Q(seats__booking__isnull=True)))
    query = request.GET.get("q", "").strip()
    if query:
        movies = movies.filter(Q(title__icontains=query) | Q(description__icontains=query))
    return render(request, "bookings/movie_list.html", {"movies": movies, "query": query})


def signup(request):
    if request.user.is_authenticated:
        return redirect("movie_list")
    form = SignUpForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        login(request, form.save())
        messages.success(request, "Your account is ready. Pick a film and make it a movie night.")
        return redirect("movie_list")
    return render(request, "registration/signup.html", {"form": form})


@login_required
def book_seat(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    form = BookingForm(request.POST if request.method == "POST" else None, movie=movie)
    if request.method == "POST" and form.is_valid():
        try:
            booking = reserve_seat(movie=movie, seat=form.cleaned_data["seat"], user=request.user)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, f"You're booked! {movie.title}, seat {booking.seat.seat_number}.")
            return redirect("booking_history")
    seats = movie.seats.select_related("booking")
    return render(request, "bookings/seat_booking.html", {
        "movie": movie, "seats": seats, "form": form,
        "available_count": movie.seats.filter(booking__isnull=True).count(),
    })


@login_required
def booking_history(request):
    bookings = Booking.objects.filter(user=request.user).select_related("movie", "seat")
    return render(request, "bookings/booking_history.html", {"bookings": bookings})


@login_required
@require_POST
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    title, seat = booking.movie.title, booking.seat.seat_number
    booking.delete()
    messages.success(request, f"Canceled {title}, seat {seat}. The seat is available again.")
    return redirect("booking_history")


def health(request):
    # A database query makes this a useful readiness check for Render.
    Movie.objects.exists()
    return JsonResponse({"status": "ok"})
