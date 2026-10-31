"""python manage.py seed_whiteleaf  — loads the content that used to live in the HTML files and admin.js."""
import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import FAQ, Attraction, Facility, Feature, HotelInfo, SiteText
from core.text_defaults import TEXT_DEFAULTS
from reviews.models import Review
from rooms.amenity_defaults import AMENITIES
from rooms.models import Amenity, Room, RoomImage
from tariffs.models import TariffItem, TariffSection

U = "https://images.unsplash.com/"
Q = "?auto=format&fit=crop&w=1200&q=80"

FAQS = [('What kind of rooms are available?', "Single, twin, and economy rooms today, with suites and apartments joining the roster shortly. Each listing spells out bed size, bathroom count, and what's included."), ('What are the check-in and check-out times?', 'Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.'), ('Is breakfast included in the price?', 'Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'), ('Do you offer airport pickup?', 'Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium.'), ('Can I cancel or change my booking?', 'Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione.'), ('Is there parking and Wi-Fi on site?', 'Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam.')]

FACILITIES = [("Fibre Wi-Fi", "wifi"), ("Infinity pool", "waves"), ("Fitness studio", "dumbbell"),
              ("Valet parking", "parking-circle"), ("All-day dining", "utensils-crossed"),
              ("Climate control", "wind"), ("Spa & wellness", "sparkles"), ("In-room coffee", "coffee")]

ATTRACTIONS = [
    ("Ruban Stores", U + "photo-1604719312566-8912e9227c6a?auto=format&fit=crop&w=700&q=80"),
    ("Marina Walk", U + "photo-1519567770579-c2fc5380497e?auto=format&fit=crop&w=700&q=80"),
    ("Green Market", U + "photo-1578916171728-46686eac8d58?auto=format&fit=crop&w=700&q=80"),
    ("Old Harbour Café", "https://picsum.photos/seed/harbour/700/900"),
    ("Craft Quarter", "https://picsum.photos/seed/craft/700/900"),
    ("Sunset Pier", "https://picsum.photos/seed/pier/700/900"),
]

FEATURES = [
    ("Wi-Fi & Technology", "Fibre throughout, smart TVs in every room, and a signal that actually reaches the balcony.", "#1f5d45",
     "Fibre throughout, so you stay connected from check-in to check-out", U + "photo-1631049307264-da0ec9d70304" + Q),
    ("Toiletries", "House-made bath products, refilled daily, in bottles you're welcome to take home.", "#1b3a5c",
     "House-made bath products, refilled daily", U + "photo-1618773928121-c32242e63f39" + Q),
    ("Recreation", "A pool that's warm past sunset and a gym that opens before the kitchen does.", "#5c3b1b",
     "A warm pool and a gym that opens early", U + "photo-1590490360182-c33d57733427" + Q),
    ("Convenience", "Late checkout on request, luggage storage, and a front desk that answers on the first ring.", "#4a2a52",
     "Late checkout and luggage storage when you need them", U + "photo-1566073771259-6a8506099945" + Q),
]

ROOMS = [
    dict(slug="single", name="Single Room", price=36000, tagline="Best option for solo travels and alone time",
         description="Best option for *solo travels* and *alone time*. A quiet room sized right for one, with a desk that actually gets used.",
         bed="One Single", tv=True, featured=True,
         images=[U + "photo-1618773928121-c32242e63f39" + Q, U + "photo-1631049307264-da0ec9d70304" + Q, U + "photo-1590490360182-c33d57733427" + Q]),
    dict(slug="twin", name="Twin Room", price=46000, tagline="Best option for lodging with a friend or family member",
         description="Best option for lodging with a *friend* or *family member*.", bed="Two Single", tv=True, featured=True,
         images=[U + "photo-1566073771259-6a8506099945" + Q]),
    dict(slug="economy", name="Single Room (Economy)", price=28000, tagline="Best option for solo travels and alone time",
         description="Best option for *solo travels* and *alone time*.", bed="One Single", tv=False, featured=True,
         images=[U + "photo-1582719478250-c89cae4dc85b" + Q]),
]

REVIEWS = [
    ("Kate Lane", 5, "We came for a weekend and stayed for the mornings — coffee on the balcony, marina fog burning off by nine. Quiet in exactly the way we needed.", "Stayed 4 nights, Marina Suite"),
    ("Marcus Vance", 5, "The spa quiet hours are truly respected here. Unwinding after a long trek through the pines while listening to the distant waves was unforgettable.", "Stayed 3 nights, Garden Villa"),
    ("Elena & David Rostova", 5, "Breakfast served until noon is a game changer. Exceptional local pastries, warm hospitality, and pure peace throughout the resort.", "Stayed 5 nights, Waterfront Penthouse"),
]

F, N, D, I, T, FR = "fixed", "night", "day", "item", "text", "free"
TARIFFS = [
    dict(slug="intro", title="Introduction", heading="Welcome to White Leaf", icon="info", body=(
        "This guide sets out our room rates and the fees that may apply during your stay, so there are no surprises at check-out.\n\n"
        "All amounts are in Nigerian naira (₦) and are per night unless stated. The rate confirmed at booking is the rate you pay. If anything is unclear, our front desk is happy to explain before you book.")),
    dict(slug="rooms", title="Room rates", icon="bed-double", rates=True,
         body="Rates include Wi-Fi, housekeeping and access to the hotel facilities listed on each room page."),
    dict(slug="times", title="Check-in and check-out", icon="clock",
         body="Check-in opens at {check_in} and check-out is by {check_out}.", items=[
        ("Early check-in (before 12:00 PM)", "Subject to availability", T, None, "50% of room rate"),
        ("Late check-out (until 3:00 PM)", "Request at the front desk", F, 5000, ""),
        ("Late check-out (after 3:00 PM)", "Charged as an extra night", T, None, "Full night’s rate")]),
    dict(slug="keys", title="Lost key cards", icon="key-round",
         body="Key cards are programmed for your stay only. Please return them at check-out.", items=[
        ("Lost key card replacement", "The old card is deactivated immediately", F, 5000, ""),
        ("Damaged key card", "Replaced when you return the damaged card", F, 3000, ""),
        ("Key card not returned at check-out", "Added to your final bill", F, 5000, ""),
        ("Locked out of your room", "Front desk assists 24 hours, ID required", FR, None, "")]),
    dict(slug="cars", title="Parking and overnight car stay", icon="car",
         body="Our secured car park is open to guests and visitors.",
         footnote="The hotel is not liable for items left inside vehicles.", items=[
        ("Guest vehicle (one per room)", "For the length of your stay", FR, None, ""),
        ("Additional guest vehicle", "", N, 3000, ""),
        ("Visitor vehicle, overnight", "Register at reception before 8:00 PM", N, 5000, ""),
        ("Visitor vehicle, daytime", "Up to 6 hours", F, 1000, ""),
        ("Vehicle left after check-out", "Please collect within 24 hours", D, 5000, "")]),
    dict(slug="guests", title="Extra guests and beds", icon="users", items=[
        ("Extra bed", "", N, 8000, ""), ("Additional adult guest", "", N, 6000, ""),
        ("Child under 5", "Using existing bedding", FR, None, "")]),
    dict(slug="damage", title="Damages and cleaning", icon="shield-alert", items=[
        ("Smoking in a non-smoking room", "Deep-cleaning fee", F, 50000, ""),
        ("Excessive cleaning", "", F, 15000, ""),
        ("Missing towel or linen", "", I, 6000, ""),
        ("Damaged furniture or fittings", "Assessed by housekeeping", T, None, "Replacement cost")]),
    dict(slug="cancel", title="Cancellations and no-shows", icon="calendar-x", body=(
        "Cancel free of charge up to 48 hours before arrival. Within 48 hours, the first night is charged. For a no-show, the first night is charged and the rest of the booking is released.")),
    dict(slug="pay", title="Payment and deposits", icon="credit-card", body=(
        "We accept cash, card and bank transfer. A refundable deposit of ₦20,000 is taken at check-in and returned at check-out once your room has been inspected. Extra charges are settled when you check out.")),
    dict(slug="contact", title="Contact information", icon="mail", contact=True,
         body="Questions about a charge? Call {phone} or visit the front desk at {address}."),
]


class Command(BaseCommand):
    help = "Load White Leaf starter content. Safe to re-run: existing rows are left alone."

    def handle(self, *args, **opts):
        if not HotelInfo.objects.exists():
            HotelInfo.objects.create(
                name="White Leaf Hotel & Suites",
                address="No. 35 Adrere Street, Independence Layout, Enugu",
                phone="+234 787 8887 788", opening_hours="Daily: 6am – 10pm",
                check_in_time=datetime.time(14, 0), check_out_time=datetime.time(12, 0))
        for key, (label, page, default) in TEXT_DEFAULTS.items():
            SiteText.objects.get_or_create(key=key, defaults=dict(label=label, page=page, value=default))
        amenities = []
        for i, (title, description) in enumerate(AMENITIES):
            obj, _ = Amenity.objects.get_or_create(title=title, defaults={"description": description, "order": i})
            amenities.append(obj)
        if not Room.objects.exists():
            for i, r in enumerate(ROOMS):
                room = Room.objects.create(
                    slug=r["slug"], name=r["name"], tagline=r["tagline"], description=r["description"],
                    price_per_night=Decimal(r["price"]), bed=r["bed"], has_tv=r["tv"], is_featured=r["featured"],
                    order=i, status="published")
                for j, url in enumerate(r["images"]):
                    RoomImage.objects.create(room=room, external_url=url, order=j, alt_text=room.name)
                # standard room amenities; the economy room has no TV
                wanted = [a for a in amenities[:7] if r["tv"] or a.title != "Television"]
                room.amenities.set(wanted)
        if not Facility.objects.exists():
            for i, (t, icon) in enumerate(FACILITIES):
                Facility.objects.create(title=t, icon=icon, order=i)
        if not Attraction.objects.exists():
            for i, (n, url) in enumerate(ATTRACTIONS):
                Attraction.objects.create(name=n, external_url=url, order=i)
        if not Feature.objects.exists():
            for i, (t, d, c, cap, img) in enumerate(FEATURES):
                Feature.objects.create(title=t, description=d, tint=c, caption=cap, external_url=img, order=i)
        if not FAQ.objects.exists():
            for i, (q, a) in enumerate(FAQS):
                FAQ.objects.create(question=q, answer=a, order=i)
        if not Review.objects.exists():
            for n, rating, body, note in REVIEWS:
                Review.objects.create(display_name=n, rating=rating, body=body, stay_note=note, status="approved")
        if not TariffSection.objects.exists():
            for i, s in enumerate(TARIFFS):
                sec = TariffSection.objects.create(
                    slug=s["slug"], title=s["title"], heading=s.get("heading", ""), icon=s["icon"],
                    body=s.get("body", ""), footnote=s.get("footnote", ""), show_room_rates=s.get("rates", False),
                    show_contact_button=s.get("contact", False), order=i)
                for j, (name, note, ptype, amount, ptext) in enumerate(s.get("items", [])):
                    TariffItem.objects.create(section=sec, name=name, note=note, price_type=ptype,
                                              amount=amount, price_text=ptext, order=j)
        self.stdout.write(self.style.SUCCESS("White Leaf starter content loaded."))