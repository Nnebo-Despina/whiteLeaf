from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse

from core.models import FAQ, Attraction, Facility, Feature
from reviews.models import Review
from rooms.models import Room


def _review_payload(limit=8):
    return [
        {"text": r.body, "author": r.display_name, "details": r.stay_note or "Guest", "rating": r.rating}
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


def robots_txt(request):
    from django.conf import settings

    if not getattr(settings, "ALLOW_INDEXING", True):
        # staging / preview site: keep every search engine out
        return HttpResponse("User-agent: *\nDisallow: /\n", content_type="text/plain")
    lines = [
        "User-agent: *",
        "Disallow: /manage/",
        "Disallow: /reviews/submit/",
        "",
        f"Sitemap: {request.scheme}://{request.get_host()}{reverse('django.contrib.sitemaps.views.sitemap')}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
