from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.db.models import Count

from core.models import SiteImage, SiteVideo, slot_limit

IN = ("w-full bg-[#F4F0E4] rounded-xl px-3.5 py-2.5 text-sm outline-none "
      "focus:ring-2 focus:ring-[#c6a15b]/50")


class StaffAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            # same wording as a wrong password, so nobody can tell whether the account exists
            raise ValidationError("Username or password is incorrect.", code="invalid_login")


class Styled:
    """Gives every field the dashboard look."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxSelectMultiple):
                widget.attrs["class"] = "h-4 w-4 mt-0.5 shrink-0 accent-[#16302A]"
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "h-4 w-4 accent-[#16302A]"
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs["class"] = "block w-full text-sm text-[#5a5347]"
            else:
                widget.attrs["class"] = IN
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("rows", 3)


class StyledModelForm(Styled, forms.ModelForm):
    pass


class SiteTextForm(Styled, forms.Form):
    text = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), required=False, label="Text")


class SiteImageForm(StyledModelForm):
    """Only offers the spots that still have room, so you can't overfill one."""

    class Meta:
        model = SiteImage
        fields = ["title", "slot", "image", "alt_text"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        used = dict(SiteImage.objects.values_list("slot").annotate(n=Count("id")))
        current = self.instance.slot if self.instance.pk else None
        free = [(value, label) for value, label in SiteImage.Slot.choices
                if used.get(value, 0) < slot_limit(value) or value == current]
        self.fields["slot"].choices = [("", "Choose where it appears")] + free
        self.fields["slot"].label = "Where it appears"
        self.fields["slot"].help_text = (
            "Each spot holds one photo. To change a spot's photo, edit the existing image."
            if free else "Every spot already has an image. Edit an existing one instead."
        )


class SiteVideoForm(StyledModelForm):
    class Meta:
        model = SiteVideo
        fields = ["title", "slot", "video"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        used = dict(SiteVideo.objects.values_list("slot").annotate(n=Count("id")))
        current = self.instance.slot if self.instance.pk else None
        free = [(v, l) for v, l in SiteVideo.Slot.choices if used.get(v, 0) < slot_limit(v) or v == current]
        self.fields["slot"].choices = [("", "Choose where it appears")] + free
        self.fields["slot"].label = "Where it appears"
        self.fields["video"].widget.attrs["accept"] = "video/mp4,video/webm"