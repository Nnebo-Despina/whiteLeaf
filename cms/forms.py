from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count

from core.models import SiteImage, SiteVideo, slot_limit

IN = (
    "w-full bg-[#F4F0E4] rounded-xl px-3.5 py-2.5 text-sm outline-none "
    "focus:ring-2 focus:ring-[#c6a15b]/50"
)


class StaffAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            # Same wording as a wrong password, so nobody can tell whether the account exists.
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


class DirectUploadModelForm(StyledModelForm):
    """Replaces Django file inputs with a hidden object path + browser upload input.

    The browser uploads the bytes directly to Supabase. Django receives only the
    resulting object path, so the Vercel function never receives the media body.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.direct_upload_fields = []

        for field_name in list(self.fields):
            try:
                model_field = self._meta.model._meta.get_field(field_name)
            except Exception:
                continue

            if not isinstance(model_field, models.FileField):
                continue

            is_video = field_name == "video"
            kind = "video" if is_video else "image"
            accept = "video/mp4,video/webm" if is_video else "image/jpeg,image/png,image/webp,image/gif"
            max_bytes = 50 * 1024 * 1024 if is_video else 20 * 1024 * 1024
            current_file = getattr(self.instance, field_name, None)
            current_path = current_file.name if current_file else ""

            # Keep the model's actual field name in POST, but make it a path field,
            # not a browser file upload field.
            self.fields[field_name] = forms.CharField(
                required=(not model_field.blank and not current_path),
                initial=current_path,
                widget=forms.HiddenInput(attrs={"class": "direct-upload-path"}),
            )

            upload_name = f"{field_name}_upload"
            self.fields[upload_name] = forms.FileField(
                required=False,
                label=f"Upload {kind}",
                widget=forms.ClearableFileInput(attrs={
                    "class": "direct-upload-input block w-full text-sm text-[#5a5347]",
                    "accept": accept,
                    "data-media-kind": kind,
                    "data-max-bytes": str(max_bytes),
                    "data-upload-target": f"{self._meta.model._meta.label_lower}.{field_name}",
                }),
            )
            self.direct_upload_fields.append(field_name)


class SiteTextForm(Styled, forms.Form):
    text = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), required=False, label="Text")


class SiteImageForm(DirectUploadModelForm):
    """Only offers the spots that still have room, so you can't overfill one."""

    class Meta:
        model = SiteImage
        fields = ["title", "slot", "image", "alt_text"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        used = dict(SiteImage.objects.values_list("slot").annotate(n=Count("id")))
        current = self.instance.slot if self.instance.pk else None
        free = [
            (value, label)
            for value, label in SiteImage.Slot.choices
            if used.get(value, 0) < slot_limit(value) or value == current
        ]
        self.fields["slot"].choices = [("", "Choose where it appears")] + free
        self.fields["slot"].label = "Where it appears"
        self.fields["slot"].help_text = (
            "Each spot holds one photo. To change a spot's photo, edit the existing image."
            if free else "Every spot already has an image. Edit an existing one instead."
        )


class SiteVideoForm(DirectUploadModelForm):
    class Meta:
        model = SiteVideo
        fields = ["title", "slot", "video"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        used = dict(SiteVideo.objects.values_list("slot").annotate(n=Count("id")))
        current = self.instance.slot if self.instance.pk else None
        free = [
            (value, label)
            for value, label in SiteVideo.Slot.choices
            if used.get(value, 0) < slot_limit(value) or value == current
        ]
        self.fields["slot"].choices = [("", "Choose where it appears")] + free
        self.fields["slot"].label = "Where it appears"