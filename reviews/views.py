from django.shortcuts import render

from core.models import FAQ, Attraction, Facility, Feature
from reviews.models import Review
from rooms.models import Room
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from .forms import ReviewForm


@require_POST
@ratelimit(key="ip", rate="3/h", method="POST", block=False)
def submit_review(request):
    if getattr(request, "limited", False):
        return JsonResponse({"ok": False, "error": "Too many reviews from this connection. Please try again later."}, status=429)
    form = ReviewForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    if form.cleaned_data.get("website"):
        # Honeypot filled in: pretend it worked, save nothing.
        return JsonResponse({"ok": True})
    form.save()  # status defaults to "pending"
    return JsonResponse({"ok": True})


def _review_payload(limit=8):
    return [
        {"text": r.body, "author": r.display_name, "details": r.stay_note or "Guest"}
        for r in Review.objects.approved()[:limit]
    ]


def home(request):
    featured = list(Room.published.filter(is_featured=True)[:4]) or list(Room.published.all()[:4])
    reviews = _review_payload()
    return render(request, "core/home.html", {
        "featured_rooms": featured,
        "reviews_json": reviews,
        "first_review": reviews[0] if reviews else None,
        "facilities": Facility.objects.filter(is_published=True),
        "attractions": Attraction.objects.filter(is_published=True),
    })


def about(request):
    return render(request, "core/about.html", {
        "features": Feature.objects.filter(is_published=True),
        "reviews": _review_payload(),
        "faqs": FAQ.objects.filter(is_published=True),
    })


def contact(request):
    return render(request, "core/contact.html")
