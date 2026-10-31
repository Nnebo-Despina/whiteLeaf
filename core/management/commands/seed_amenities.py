"""python manage.py seed_amenities  — adds the starter room amenities (safe to re-run)."""
from django.core.management.base import BaseCommand

from rooms.amenity_defaults import AMENITIES
from rooms.models import Amenity


class Command(BaseCommand):
    help = "Create the starter room amenities that don't exist yet."

    def handle(self, *args, **opts):
        made = 0
        for i, (title, description) in enumerate(AMENITIES):
            _, created = Amenity.objects.get_or_create(title=title, defaults={"description": description, "order": i})
            made += created
        self.stdout.write(self.style.SUCCESS(f"{made} amenities added, {len(AMENITIES) - made} already existed."))
