
from django.urls import path

from . import views

app_name = "rooms"

urlpatterns = [
    path("", views.room_list, name="list"),

    # Temporary permission for direct Supabase uploads.
    path(
        "video-upload-token/",
        views.create_video_upload_url,
        name="video_upload_token",
    ),

    path("<slug:slug>/", views.room_detail, name="detail"),
]
