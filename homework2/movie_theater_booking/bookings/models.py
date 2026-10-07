"""One seat inventory per movie; each movie represents one screening."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    release_date = models.DateField()
    duration = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Minutes")

    class Meta:
        ordering = ["id"]
        constraints = [models.CheckConstraint(condition=models.Q(duration__gt=0), name="positive_movie_duration")]

    def __str__(self):
        return self.title


class Seat(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="seats")
    seat_number = models.CharField(max_length=4, validators=[RegexValidator(r"^[A-Z][1-9][0-9]?$", "Use a row letter and seat number, such as A1.")])

    class Meta:
        ordering = ["seat_number"]
        constraints = [models.UniqueConstraint(fields=["movie", "seat_number"], name="unique_movie_seat")]

    @property
    def booking_status(self):
        # Derived from the reservation so status cannot drift from actual bookings.
        return hasattr(self, "booking")

    def __str__(self):
        return f"{self.movie}: {self.seat_number}"


class Booking(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="bookings")
    seat = models.OneToOneField(Seat, on_delete=models.CASCADE, related_name="booking")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    booking_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-booking_date", "-id"]

    def clean(self):
        if self.seat_id and self.movie_id and self.seat.movie_id != self.movie_id:
            raise ValidationError({"seat": "This seat belongs to a different movie."})

    def __str__(self):
        return f"{self.movie} / {self.seat.seat_number} / {self.user}"
