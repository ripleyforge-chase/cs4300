from django.contrib import admin
from .models import Booking, Movie, Seat


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ["title", "release_date", "duration"]
    search_fields = ["title"]


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ["seat_number", "movie", "booking_status"]
    list_filter = ["movie"]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["movie", "seat", "user", "booking_date"]
    readonly_fields = ["movie", "seat", "user", "booking_date"]

    def has_add_permission(self, request):
        return False
