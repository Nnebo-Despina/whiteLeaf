from django.shortcuts import render

from rooms.models import Room

from .models import TariffSection


def tariffs(request):
    sections = TariffSection.objects.filter(is_published=True).prefetch_related("items")
    return render(request, "tariffs/tariffs.html", {
        "sections": sections,
        "rooms": Room.published.all(),
    })
