import re

from django import template
from django.utils.html import conditional_escape, escape
from django.utils.safestring import mark_safe

from core.models import SiteImage, SiteText, SiteVideo
from core.text_defaults import TEXT_DEFAULTS

register = template.Library()


def _request_cache(context, attr, loader):
    request = context.get("request")
    if request is None:
        return loader()
    if not hasattr(request, attr):
        setattr(request, attr, loader())
    return getattr(request, attr)


@register.simple_tag(takes_context=True)
def st(context, key):
    """Editable site text: live value from the database, else the built-in default."""
    texts = _request_cache(context, "_site_texts", lambda: dict(SiteText.objects.values_list("key", "value")))
    value = texts.get(key)
    if value:
        return value
    return TEXT_DEFAULTS.get(key, ("", "", ""))[2]


@register.simple_tag(takes_context=True)
def site_image(context, slot, fallback=""):
    """URL of the latest published image for a slot, else the fallback."""

    def load():
        found = {}
        for img in SiteImage.objects.filter(status="published").order_by("updated_at"):
            found[img.slot] = img.image.url  # later (newer) rows overwrite earlier ones
        return found

    images = _request_cache(context, "_site_images", load)
    return images.get(slot) or fallback


def _clock(t):
    """2:00 PM style time. Avoids strftime's %-I, which fails on Windows."""
    return t.strftime("%I:%M %p").lstrip("0") if t else ""


@register.simple_tag(takes_context=True)
def fill(context, text):
    """Swap {phone}, {address}, {check_in}, {check_out} in tariff text for live hotel info."""
    hotel = context.get("hotel")
    if not hotel:
        return text
    out = hotel.check_out_time
    values = {
        "phone": hotel.phone,
        "address": hotel.address,
        "check_in": _clock(hotel.check_in_time),
        "check_out": "12:00 noon" if out and out.hour == 12 and out.minute == 0 else _clock(out),
    }
    for k, v in values.items():
        text = text.replace("{" + k + "}", v)
    return text


@register.filter
def gold(value):
    """*word* -> gold-highlighted word."""
    return mark_safe(re.sub(r"\*(.+?)\*", r'<span class="gold-text">\1</span>', escape(value)))


@register.filter
def emph(value):
    """*phrase* -> bold phrase."""
    return mark_safe(
        re.sub(r"\*(.+?)\*", r'<span class="font-semibold text-[#241F18]">\1</span>', escape(value))
    )


@register.filter
def naira(value):
    try:
        return f"₦{float(value):,.0f}"
    except (TypeError, ValueError):
        return ""


@register.filter
def zpad(value, width=2):
    return str(value).zfill(int(width))


_STAR = (
    '<svg viewBox="0 0 24 24" class="{size} {tone}" fill="{fill}" stroke="currentColor" stroke-width="1.3" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
)


@register.simple_tag
def rating_stars(rating, size="w-4 h-4", empty="text-[#e2dcc8]"):
    """Five stars, `rating` of them filled gold. `empty` is the colour class of the unfilled ones."""
    try:
        rating = max(0, min(5, int(rating)))
    except (TypeError, ValueError):
        rating = 0
    stars = "".join(
        _STAR.format(size=size, tone="text-[#c6a15b]" if i <= rating else empty, fill="#c6a15b" if i <= rating else "none")
        for i in range(1, 6)
    )
    return mark_safe(f'<span class="inline-flex gap-0.5" role="img" aria-label="{rating} out of 5 stars">{stars}</span>')


@register.simple_tag(takes_context=True)
def site_video(context, slot, fallback=""):
    """URL of the latest published video for a slot, else the fallback."""

    def load():
        found = {}
        for v in SiteVideo.objects.filter(status="published").order_by("updated_at"):
            found[v.slot] = v.video.url
        return found

    videos = _request_cache(context, "_site_videos", load)
    return videos.get(slot) or fallback