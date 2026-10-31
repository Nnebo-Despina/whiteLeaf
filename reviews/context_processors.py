from core.models import HotelInfo

NAV = [
    ("home", "Home", ("home",)),
    ("rooms", "Accommodations", ("rooms:list", "rooms:detail")),
    ("tariffs", "Tariffs", ("tariffs",)),
    ("about", "About", ("about",)),
    ("contact", "Contact", ("contact",)),
]
NAV_URLS = {"home": "home", "rooms": "rooms:list", "tariffs": "tariffs", "about": "about", "contact": "contact"}
OVERLAY_PAGES = {"home", "about", "tariffs"}


def site(request):
    match = getattr(request, "resolver_match", None)
    view_name = match.view_name if match else ""
    active = next((key for key, _, names in NAV if view_name in names), "")
    return {
        "hotel": HotelInfo.load(),
        "nav_links": [(key, label, NAV_URLS[key], key == active) for key, label, _ in NAV],
        "nav_overlay": view_name in OVERLAY_PAGES,
    }
