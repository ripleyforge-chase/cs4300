from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Booking, Movie, Seat
from .serializers import BookingSerializer, MovieSerializer, SeatSerializer


class StaffWriteOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or request.user.is_staff


class MovieViewSet(viewsets.ModelViewSet):
    """Expose the movie catalog publicly and reserve CRUD writes for staff."""

    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [StaffWriteOrReadOnly]


class SeatViewSet(viewsets.ReadOnlyModelViewSet):
    """List availability by movie and let signed-in users reserve a seat.

    Booking goes through the shared serializer/service instead of allowing direct
    changes to the derived booking status.
    """

    serializer_class = SeatSerializer

    def get_queryset(self):
        seats = Seat.objects.select_related("booking", "movie")
        movie = self.request.query_params.get("movie")
        if movie is not None:
            try:
                movie = int(movie)
                if movie < 1:
                    raise ValueError
            except ValueError:
                raise ValidationError({"movie": "Use a positive movie ID."}) from None
            seats = seats.filter(movie_id=movie)
        return seats

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def book(self, request, pk=None):
        seat = self.get_object()
        serializer = BookingSerializer(data={"movie": seat.movie_id, "seat": seat.pk}, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BookingViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                     mixins.RetrieveModelMixin, mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    """Create, list, retrieve, and cancel only the signed-in user's bookings.

    Filtering the queryset also prevents access to another user's ticket by ID.
    Existing reservations cannot be reassigned through update endpoints.
    """

    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related("movie", "seat")
