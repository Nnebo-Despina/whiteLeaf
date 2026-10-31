"""Every piece of editable page copy: key -> (label, page, default text).

The `{% st "key" %}` template tag falls back to the default here, so the
site works even before anything is saved in the database.
Wrap a word in *stars* where the page shows a gold highlight.
"""

TEXT_DEFAULTS = {
    # ---- Home ----
    "hero.title": ("Homepage headline", "home", "Find your *best* stay"),
    "hero.sub": ("Homepage intro", "home",
        "Suites overlooking the marina, a quiet spa, and a kitchen that cooks like it means it — twenty minutes from the old town."),
    "welcome.eyebrow": ("Welcome small heading", "home", "RAISING COMFORT TO THE HIGHEST LEVEL"),
    "welcome.title": ("Welcome heading", "home", "Welcome to White Leaf"),
    "welcome.body": ("Welcome message", "home",
        "White Leaf sits where the marina meets the pines. Every suite opens onto water or garden, breakfast runs until noon, and the spa keeps quiet hours for exactly that reason — quiet."),
    "rooms.title": ("Accommodations heading", "home", "Our accommodations"),
    "rooms.sub": ("Accommodations intro", "home",
        "Four suite types, each with its own light and its own view — pick the one that matches the trip you're actually taking."),
    "bar.title": ("Bar heading", "home", "Our bar"),
    "bar.body": ("Bar text (first paragraph)", "home",
        "Open from five, closing whenever the last conversation does. The list leans local — foraged bitters, a house gin, wine from three vineyards up the coast."),
    "bar.body2": ("Bar text (second paragraph)", "home",
        "No dress code, no rush. Ask the bartender for something off the menu — that's usually the better drink anyway."),
    "amenities.title": ("Hotel amenities heading", "home", "Hotel amenities"),
    "amenities.sub": ("Hotel amenities intro", "home",
        "Everything below is included in the room rate — nothing here is an upsell."),
    "nearby.eyebrow": ("Nearby small heading", "home", "NEARBY, WORTH THE WALK"),
    "nearby.title": ("Nearby heading", "home", "Discover Nearby Attractions For Your Stay"),
    "cta.title": ("Call-to-action heading", "home", "Ready for a proper stay?"),
    "cta.body": ("Call-to-action text", "home",
        "Rooms are limited during marina season — the earlier you book, the better the view."),
    # ---- About ----
    "about.title": ("About page title", "about", "White Leaf Hotel"),
    "about.sub": ("About page intro", "about",
        "Located at the heart of Enugu — quiet rooms, a proper kitchen, and staff who remember your name by the second morning."),
    "care.title": ("Service heading", "about", "Dedicated to serving you"),
    "care.sub": ("Service intro", "about",
        "Located at the heart of Enugu, run by people who'd rather get the small things right than promise the big ones."),
    "care.caption": ("Service photo caption", "about",
        "We take special care of our guests, attending to them and answering queries"),
    "stat1.value": ("Statistic 1 number", "about", "15,000+"),
    "stat1.label": ("Statistic 1 label", "about", "guests attended to"),
    "stat2.value": ("Statistic 2 number", "about", "50+"),
    "stat2.label": ("Statistic 2 label", "about", "rooms to pick from"),
    "stat3.value": ("Statistic 3 number", "about", "99%"),
    "stat3.label": ("Statistic 3 label", "about", "satisfaction rate"),
    "staff.title": ("Staff heading", "about", "Meet our staff"),
    "staff.body": ("Meet our staff text", "about",
        "Most of the front-of-house team have been here since we opened — they know which room gets morning light and who prefers a quiet corner without being asked twice."),
    "staff.body2": ("Meet our staff text (second paragraph)", "about",
        "Housekeeping, the kitchen, and the concierge desk all report in every morning, so nothing about your stay is handed off between shifts."),
    "faq.title": ("FAQ heading", "about", "Frequently asked questions"),
    "faq.sub": ("FAQ intro", "about",
        "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."),
    "faq.card": ("FAQ 'still have questions' text", "about",
        "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum."),
}
