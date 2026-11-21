
from django import forms
from django.contrib import admin

from .models import Amenity, Room, RoomImage


class RoomImageAdminForm(forms.ModelForm):
    # The actual FileField is represented by a hidden path field.
    video = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    # This file input is used only by the browser upload script.
    video_upload = forms.FileField(
        required=False,
        label="Upload room video (MP4)",
        widget=forms.FileInput(attrs={
            "accept": "video/mp4,.mp4",
            "class": "direct-video-upload",
        }),
    )

    class Meta:
        model = RoomImage
        fields = "__all__"

    def clean_video_upload(self):
        uploaded_file = self.cleaned_data.get("video_upload")

        if uploaded_file:
            if not uploaded_file.name.lower().endswith(".mp4"):
                raise forms.ValidationError("Only MP4 videos are supported.")

            if uploaded_file.size > 500 * 1024 * 1024:
                raise forms.ValidationError(
                    "Video cannot exceed 500 MB."
                )

        return uploaded_file

    def save(self, commit=True):
        instance = super().save(commit=False)

        # video contains the path returned by the upload endpoint.
        if commit:
            instance.save()
            self.save_m2m()

        return instance


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    form = RoomImageAdminForm
    extra = 1

    fields = (
        "image",
        "external_url",
        "video",
        "video_upload",
        "alt_text",
        "order",
    )

    class Media:
        js = (
            "rooms/js/direct-upload.js",
        )


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
