from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Seat


class SignUpForm(UserCreationForm):
    """No email or personal information is needed for this class demo."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class BookingForm(forms.Form):
    seat = forms.ModelChoiceField(queryset=Seat.objects.none(), empty_label=None)

    def __init__(self, *args, movie, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["seat"].queryset = movie.seats.filter(booking__isnull=True)
        self.fields["seat"].error_messages["invalid_choice"] = "That seat is unavailable. Please choose another."
