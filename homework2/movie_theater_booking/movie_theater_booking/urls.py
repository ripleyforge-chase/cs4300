from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from bookings.api import BookingViewSet, MovieViewSet, SeatViewSet

router = DefaultRouter()
router.register("movies", MovieViewSet)
router.register("seats", SeatViewSet, basename="seat")
router.register("bookings", BookingViewSet, basename="booking")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
]
