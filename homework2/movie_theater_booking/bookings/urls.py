from django.urls import path
from . import views

urlpatterns = [
    path("", views.movie_list, name="movie_list"),
    path("movies/<int:movie_id>/book/", views.book_seat, name="book_seat"),
    path("bookings/", views.booking_history, name="booking_history"),
    path("bookings/<int:booking_id>/cancel/", views.cancel_booking, name="cancel_booking"),
    path("accounts/signup/", views.signup, name="signup"),
    path("health/", views.health, name="health"),
]
