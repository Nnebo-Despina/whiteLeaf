import re

from django import forms
from django.utils import timezone

from rooms.models import Room

from .models import BookingRequest


def _choices(start, stop, blank="Select"):
    return [("", blank)] + [(i, str(i)) for i in range(start, stop + 1)]


class RoomChoice(forms.ModelChoiceField):
    def label_from_instance(self, room):
        return f"{room.name} — ₦{room.price_per_night:,.0f} / night"


class BookingForm(forms.ModelForm):
    adults = forms.TypedChoiceField(choices=_choices(1, 10), coerce=int, empty_value=None, label="Adult")
    children = forms.TypedChoiceField(choices=_choices(0, 10), coerce=int, empty_value=0, required=False, label="Children")
    room = RoomChoice(queryset=Room.published.none(), required=False, empty_label="Select room", label="Room Type")
    website = forms.CharField(required=False)  # honeypot: real people never fill this in

    class Meta:
        model = BookingRequest
        fields = ["name", "phone", "check_in", "check_out", "adults", "children", "room"]
        labels = {"name": "Name", "phone": "Phone Number", "check_in": "Check-in Date", "check_out": "Check-out Date"}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your full name", "autocomplete": "name"}),
            "phone": forms.TextInput(attrs={"placeholder": "+234 801 234 5678", "autocomplete": "tel", "inputmode": "tel"}),
            "check_in": forms.DateInput(attrs={"type": "date"}),
            "check_out": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            base = "h-11 w-full rounded-xl bg-[#F1F1EC] px-4 text-sm text-[#241F18] outline-none transition focus:ring-2 focus:ring-[#c6a15b]/50 placeholder:text-[#9a9486]"
            if isinstance(field.widget, forms.Select):
                base += " appearance-none pr-10"
            field.widget.attrs["class"] = base
        self.fields["website"].widget.attrs.update({"class": "", "tabindex": "-1", "autocomplete": "off", "aria-hidden": "true"})
        self.fields["room"].queryset = Room.published.all()
        self.fields["check_in"].widget.attrs["min"] = timezone.localdate().isoformat()
        self.fields["check_out"].widget.attrs["min"] = timezone.localdate().isoformat()

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        if len(name) < 2:
            raise forms.ValidationError("Please enter your full name.")
        return name

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = re.sub(r"\D", "", phone)
        if not (7 <= len(digits) <= 15) or not re.fullmatch(r"[\d\s+()\-]+", phone):
            raise forms.ValidationError("Enter a phone number we can reach you on.")
        return phone

    def clean_check_in(self):
        day = self.cleaned_data["check_in"]
        if day < timezone.localdate():
            raise forms.ValidationError("Check-in can't be in the past.")
        return day

    def clean(self):
        data = super().clean()
        check_in, check_out = data.get("check_in"), data.get("check_out")
        if check_in and check_out and check_out <= check_in:
            self.add_error("check_out", "Check-out must be after check-in.")
        return data
