from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction
from bookings.models import Movie, Seat

MOVIES = [
    ("The Last Orbit", "An astronaut follows a mysterious signal beyond the edge of the known solar system, where getting home means letting go.", date(2026, 8, 14), 118),
    ("Coastline", "Two estranged sisters take the long way home along the Pacific coast. A warm, quietly funny story about finding common ground.", date(2026, 9, 4), 104),
    ("Midnight Express", "A night-shift conductor discovers that one passenger has vanished from a train that has never stopped. Every carriage holds a clue.", date(2026, 10, 2), 126),
]


class Command(BaseCommand):
    help = "Create three fictional movies and 32 seats each, without resetting users or bookings."

    @transaction.atomic
    def handle(self, *args, **options):
        for title, description, release_date, duration in MOVIES:
            movie, _ = Movie.objects.get_or_create(title=title, defaults={
                "description": description, "release_date": release_date, "duration": duration,
            })
            for row in "ABCD":
                for number in range(1, 9):
                    Seat.objects.get_or_create(movie=movie, seat_number=f"{row}{number}")
        self.stdout.write(self.style.SUCCESS("Demo ready: 3 fictional movies, 32 seats per movie."))
