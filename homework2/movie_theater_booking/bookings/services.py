"""Reservation rules shared by the API and Django template views."""
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .models import Booking


def reserve_seat(*, movie, seat, user):
    if seat.movie_id != movie.pk:
        raise ValidationError("This seat belongs to a different movie.")
    try:
        # The database's unique seat constraint is the final arbiter of races.
        with transaction.atomic():
            return Booking.objects.create(movie=movie, seat=seat, user=user)
    except IntegrityError:
        if Booking.objects.filter(seat=seat).exists():
            raise ValidationError("That seat has just been booked. Please choose another.") from None
        raise
