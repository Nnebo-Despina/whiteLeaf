"""One entry per editable thing in the dashboard."""
from dataclasses import dataclass, field

from core.models import FAQ, Attraction, Facility, Feature, SiteImage, SiteText, SiteVideo
from reviews.models import Review

from .forms import SiteImageForm, SiteVideoForm
from rooms.models import Amenity, Room, RoomImage
from tariffs.models import TariffItem, TariffSection


@dataclass
class Section:
    slug: str
    model: type
    label: str
    singular: str
    icon: str
    desc: str
    fields: list
    mode: str = "bool"            # "status" | "bool" | "review" | "text"
    can_add: bool = True
    can_delete: bool = True
    inlines: list = field(default_factory=list)   # (model, fields, heading)
    group: str = "Content"
    form: type = None               # optional custom ModelForm


SECTIONS = [
    Section("text", SiteText, "Website text", "text block", "type",
            "Edit the wording shown across your pages.", [], mode="text", can_add=False, can_delete=False),
    Section("images", SiteImage, "Images", "image", "image",
            "Upload photos and choose where they appear.", ["title", "slot", "image", "alt_text"], mode="status", form=SiteImageForm),
    Section("videos", SiteVideo, "Videos", "video", "video",
            "Upload the promo video shown on the home page.", ["title", "slot", "video"], mode="status",
            form=SiteVideoForm),
    Section("rooms", Room, "Rooms", "room", "bed-double",
            "Update rates, descriptions, photos and availability.",
            ["name", "slug", "category", "tagline", "description", "card_note", "price_per_night", "bed",
             "bathrooms", "size_sqm", "has_wifi", "has_tv", "amenities", "cleanliness_note", "amenities_note",
             "availability", "is_featured", "order"], mode="status",
            inlines=[(RoomImage, ["image", "external_url", "alt_text", "order"], "Photos")]),
    Section("amenities", Amenity, "Room amenities", "amenity", "list-checks",
            "Create each amenity once, then tick it on any room.",
            ["title", "description", "order", "is_published"]),
    Section("tariffs", TariffSection, "Tariffs", "tariff section", "receipt",
            "Rates, fees and policies shown on the Tariffs page.",
            ["title", "heading", "slug", "icon", "body", "footnote", "show_room_rates",
             "show_contact_button", "order", "is_published"],
            inlines=[(TariffItem, ["name", "note", "price_type", "amount", "price_text", "order"], "Fees in this section")]),
    Section("reviews", Review, "Reviews", "review", "message-square",
            "Approve guest reviews before they appear on the site.",
            ["display_name", "rating", "body", "stay_note", "is_featured"], mode="review", can_add=False),
    Section("faqs", FAQ, "FAQs", "FAQ", "circle-help", "Questions shown on the About page.",
            ["question", "answer", "order", "is_published"], group="Extras"),
    Section("facilities", Facility, "Hotel amenities", "amenity", "sparkles", "The icon grid on the home page.",
            ["title", "icon", "order", "is_published"], group="Extras"),
    Section("nearby", Attraction, "Nearby places", "place", "map-pin", "Cards in the home page's Nearby section.",
            ["name", "image", "external_url", "order", "is_published"], group="Extras"),
    Section("features", Feature, "About features", "feature", "layout-grid", "The four rotating columns on the About page, with the photo and caption each one shows.",
            ["title", "description", "caption", "image", "external_url", "tint", "order", "is_published"], group="Extras"),
]
BY_SLUG = {s.slug: s for s in SECTIONS}