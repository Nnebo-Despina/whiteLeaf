from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from bookings.forms import BookingForm

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


@ratelimit(key="ip", rate="8/h", method="POST", block=False)
def contact(request):
    """Contact & Booking page: the booking form on top, hotel details, map and review form below."""
    limited = False
    booking_done = None
    if request.method == "POST":
        form = BookingForm(request.POST)
        if getattr(request, "limited", False):
            limited = True
        elif form.is_valid():
            if form.cleaned_data.get("website"):
                return redirect(f"{reverse('contact')}?booked=1#book")  # bot: pretend it worked, save nothing
            booking = form.save()
            request.session["last_booking"] = booking.pk
            _notify_hotel(booking)
            return redirect(f"{reverse('contact')}?booked=1#book")
    else:
        initial = {}
        slug = request.GET.get("room")
        if slug:
            from rooms.models import Room

            room = Room.published.filter(slug=slug).first()
            if room:
                initial["room"] = room.pk
        form = BookingForm(initial=initial)
        if request.GET.get("booked"):
            from bookings.models import BookingRequest

            booking_done = BookingRequest.objects.filter(pk=request.session.pop("last_booking", None)).first() or True
    return render(request, "core/contact.html", {
        "form": form, "limited": limited, "booking_done": booking_done, "today": timezone.localdate().isoformat(),
    })


def _notify_hotel(booking):
    email = getattr(settings, "BOOKING_NOTIFY_EMAIL", "")
    if not email:
        return
    send_mail(
        f"New booking request {booking.reference}: {booking.name}",
        f"{booking.name} ({booking.phone}) would like {booking.room_label}\n"
        f"{booking.check_in:%d %b %Y} to {booking.check_out:%d %b %Y} ({booking.nights} nights)\n"
        f"{booking.adults} adult(s), {booking.children} child(ren)\n\n"
        "Open your dashboard > Bookings to reply.",
        None, [email], fail_silently=True,
    )


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


def custom_404(request, exception):
    context = {
        "nav_overlay": False,
        # same nav_links structure your other views pass, with active=False for all
        "nav_links": [
            ("home", "Home", "home", False),
            ("accommodations", "Accommodations", "rooms:list", False),
            ("tariffs", "Tariffs", "tariffs", False),
            ("about", "About", "about", False),
            ("contact", "Contact", "contact", False),
        ],
    }
    return render(request, "404.html", context, status=404)
