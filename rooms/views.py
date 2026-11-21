from django.core.paginator import Paginator
from django.db.models import F, Prefetch
from django.db.models.functions import Abs
from django.shortcuts import get_object_or_404, render

from .models import Amenity, Room

PER_PAGE = 6


def room_list(request):
    category = request.GET.get("category", Room.Category.ROOM)
    if category not in Room.Category.values:
        category = Room.Category.ROOM
    qs = Room.published.filter(category=category).prefetch_related("images")
    page = Paginator(qs, PER_PAGE).get_page(request.GET.get("page"))
    tabs = [(value, label, value == category) for value, label in Room.Category.choices]
    return render(request, "rooms/list.html", {
        "page": page, "tabs": tabs, "category": category,
        "category_label": Room.Category(category).label,
    })


def room_detail(request, slug):
    room = get_object_or_404(
        Room.published.prefetch_related(
            "images", Prefetch("amenities", queryset=Amenity.objects.filter(is_published=True))
        ),
        slug=slug,
    )
    # the 4 published rooms whose price is closest to this one (ties: your own room order)
    similar = (
        Room.published.exclude(pk=room.pk)
        .annotate(price_gap=Abs(F("price_per_night") - room.price_per_night))
        .order_by("price_gap", "order", "id")
        .prefetch_related("images")[:4]
    )
    return render(request, "rooms/detail.html", {"room": room, "similar_rooms": similar})




import json
import uuid
import urllib.error
import urllib.request

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@staff_member_required
@require_POST
def create_video_upload_url(request):
    """
    Generate a temporary Supabase upload permission.

    The video itself never passes through Django.
    """

    # Check Supabase configuration.
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return JsonResponse(
            {"error": "Supabase upload configuration is incomplete."},
            status=503,
        )

    if not settings.SUPABASE_ANON_KEY:
        return JsonResponse(
            {"error": "Supabase anon key is not configured."},
            status=503,
        )

    # Read and validate upload information.
    try:
        data = json.loads(request.body)
        filename = data.get("filename", "")
        size = int(data.get("size", 0))
        content_type = data.get("content_type", "")
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({"error": "Invalid upload information."}, status=400)

    if not filename.lower().endswith(".mp4"):
        return JsonResponse(
            {"error": "Only MP4 videos are supported."},
            status=400,
        )

    if size <= 0 or size > settings.ROOM_VIDEO_MAX_SIZE:
        return JsonResponse(
            {"error": "Video must be between 1 byte and 500 MB."},
            status=400,
        )

    if content_type not in ("video/mp4", "application/octet-stream"):
        return JsonResponse(
            {"error": "Invalid video content type."},
            status=400,
        )

    # Generate a unique storage path.
    object_path = f"rooms/videos/{uuid.uuid4().hex}.mp4"

    bucket = settings.SUPABASE_MEDIA_BUCKET

    endpoint = (
        f"{settings.SUPABASE_URL}/storage/v1"
        f"/object/upload/sign/{bucket}/{object_path}"
    )

    payload = json.dumps({"upsert": False}).encode("utf-8")

    supabase_request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": (
                f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}"
            ),
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(supabase_request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))

        signed_path = result.get("signedURL") or result.get("url")

        if not signed_path:
            raise ValueError("Supabase did not return an upload URL.")

        if signed_path.startswith("http"):
            upload_url = signed_path
        else:
            upload_url = (
                f"{settings.SUPABASE_URL}/storage/v1{signed_path}"
            )

        # Some responses return the token separately.
        token = result.get("token")

        if token and "token=" not in upload_url:
            separator = "&" if "?" in upload_url else "?"
            upload_url = f"{upload_url}{separator}token={token}"

        return JsonResponse({
            "upload_url": upload_url,
            "path": object_path,
            "api_key": settings.SUPABASE_ANON_KEY,
        })

    except urllib.error.HTTPError as error:
        return JsonResponse(
            {"error": "Supabase could not create an upload permission."},
            status=502,
        )

    except (urllib.error.URLError, TimeoutError, ValueError):
        return JsonResponse(
            {"error": "Unable to contact Supabase Storage."},
            status=502,
        )
