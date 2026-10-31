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