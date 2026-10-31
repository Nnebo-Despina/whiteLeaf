from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from rooms.models import Room


class PageSitemap(Sitemap):
    """The fixed pages."""

    changefreq = "monthly"

    PAGES = [("home", 1.0), ("rooms:list", 0.9), ("tariffs", 0.7), ("about", 0.6), ("contact", 0.6)]

    def items(self):
        return [name for name, _ in self.PAGES]

    def location(self, name):
        return reverse(name)

    def priority(self, name):
        return dict(self.PAGES)[name]


class RoomSitemap(Sitemap):
    """One entry per published room; updates itself when you add or edit rooms."""

    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Room.published.all()

    def lastmod(self, room):
        return room.updated_at


sitemaps = {"pages": PageSitemap, "rooms": RoomSitemap}
