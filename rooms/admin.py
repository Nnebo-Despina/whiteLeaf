import re

from django import forms
from django.contrib import admin
from django.urls import reverse

from .models import Amenity, Room, RoomImage

TUS_CDN = "https://cdn.jsdelivr.net/npm/tus-js-client@4/dist/tus.min.js"

IMAGE_PATH = re.compile(r"^rooms/[^/]+\.(jpe?g|png|webp|gif)$", re.I)
VIDEO_PATH = re.compile(r"^rooms/videos/[^/]+\.(mp4|webm)$", re.I)


class RoomImageAdminForm(forms.ModelForm):
    """Photos and videos go straight from the browser to Supabase.

    `image` and `video` become hidden path fields; the visible boxes are `*_upload`.
    Django only ever receives the saved path, so Vercel's request size limit is never hit.
    """

    image = forms.CharField(required=False, widget=forms.HiddenInput())
    video = forms.CharField(required=False, widget=forms.HiddenInput())

    image_upload = forms.FileField(required=False, label="Upload photo")
    video_upload = forms.FileField(required=False, label="Upload video (MP4 or WebM)")

    class Meta:
        model = RoomImage
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        token_url = reverse("cms:media_upload_token")

        def configure(name, kind, accept, max_mb):
            widget = self.fields[f"{name}_upload"].widget
            widget.attrs.update({
                "accept": accept,
                "data-media-kind": kind,
                "data-max-bytes": str(max_mb * 1024 * 1024),
                "data-upload-target": f"rooms.roomimage.{name}",
                "data-upload-token-url": token_url,
            })
            current = getattr(self.instance, name, None)
            if current:
                self.fields[f"{name}_upload"].help_text = f"Current: {current.name}"

        configure("image", "image", "image/jpeg,image/png,image/webp,image/gif", 20)
        configure("video", "video", "video/mp4,video/webm", 50)

    def _clean_path(self, name, pattern, label):
        value = (self.cleaned_data.get(name) or "").strip()
        current = getattr(self.instance, name, None)
        if value and value != (current.name if current else "") and not pattern.match(value):
            raise forms.ValidationError(f"Unexpected {label} path. Upload the file again.")
        return value

    def clean_image(self):
        return self._clean_path("image", IMAGE_PATH, "photo")

    def clean_video(self):
        return self._clean_path("video", VIDEO_PATH, "video")


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    form = RoomImageAdminForm
    extra = 1

    fields = (
        "image_upload",
        "image",
        "external_url",
        "video_upload",
        "video",
        "external_video_url",
        "alt_text",
        "order",
    )

    class Media:
        js = (TUS_CDN, "cms/js/direct-uploads.js")


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "order", "is_published")
    list_editable = ("order", "is_published")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price_per_night",
        "availability",
        "status",
    )

    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("amenities",)
    inlines = [RoomImageInline]