from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Booking, Movie, Seat
from .services import reserve_seat


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ["id", "title", "description", "release_date", "duration"]


class SeatSerializer(serializers.ModelSerializer):
    booking_status = serializers.BooleanField(read_only=True)

    class Meta:
        model = Seat
        fields = ["id", "movie", "seat_number", "booking_status"]


class BookingSerializer(serializers.ModelSerializer):
    """Validate the movie/seat pair and assign ownership from the request user."""

    movie_title = serializers.CharField(source="movie.title", read_only=True)
    seat_number = serializers.CharField(source="seat.seat_number", read_only=True)
    # Uniqueness is handled atomically by reserve_seat with a useful error.
    seat = serializers.PrimaryKeyRelatedField(queryset=Seat.objects.all())

    class Meta:
        model = Booking
        fields = ["id", "movie", "movie_title", "seat", "seat_number", "user", "booking_date"]
        read_only_fields = ["user", "booking_date"]

    def validate(self, attrs):
        if attrs["seat"].movie_id != attrs["movie"].pk:
            raise serializers.ValidationError({"seat": "This seat belongs to a different movie."})
        return attrs

    def create(self, validated_data):
        try:
            return reserve_seat(user=self.context["request"].user, **validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"seat": exc.messages}) from exc
