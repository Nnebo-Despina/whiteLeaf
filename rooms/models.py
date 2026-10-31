from django.db import models
from django.urls import reverse

from core.models import PublishStatus, TimeStamped

PLACEHOLDER = "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=800&q=80"


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=PublishStatus.PUBLISHED)


class Amenity(models.Model):
    """A reusable amenity (Air Conditioning, Wi-Fi, ...). Create each once, then tick it on any room."""

    title = models.CharField(max_length=60, unique=True)
    description = models.CharField(max_length=220)
    order = models.PositiveSmallIntegerField(default=0, help_text="Lower numbers show first")
    is_published = models.BooleanField("Show on site", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name_plural = "Amenities"

    def __str__(self):
        return self.title


class Room(TimeStamped):
    class Category(models.TextChoices):
        ROOM = "room", "Rooms"
        SUITE = "suite", "Suites"
        APARTMENT = "apartment", "Apartments"

    class Availability(models.TextChoices):
        AVAILABLE = "available", "Available"
        BOOKED = "booked", "Fully booked"

    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True, help_text="Used in the web address, e.g. single-room")
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.ROOM)
    tagline = models.CharField("Short description", max_length=160)
    description = models.TextField(
        blank=True, help_text="Shown on the room page. Wrap a phrase in *stars* to make it bold."
    )
    card_note = models.CharField(
        max_length=60, blank=True, help_text="Small line on the home page card, e.g. Garden view"
    )
    price_per_night = models.DecimalField("Price per night (₦)", max_digits=10, decimal_places=2)
    bed = models.CharField(max_length=40, help_text="e.g. One Single")
    bathrooms = models.PositiveSmallIntegerField(default=1)
    has_wifi = models.BooleanField("Wi-Fi", default=True)
    has_tv = models.BooleanField("TV", default=True)
    size_sqm = models.PositiveSmallIntegerField("Size (m²)", null=True, blank=True)
    cleanliness_note = models.TextField(
        blank=True, default="Rooms are turned over and inspected between every stay, no exceptions."
    )
    amenities_note = models.TextField(
        blank=True, default="Climate control, fresh linen, and a stocked minibar as standard."
    )
    amenities = models.ManyToManyField(Amenity, blank=True, related_name="rooms")
    availability = models.CharField(max_length=10, choices=Availability.choices, default=Availability.AVAILABLE)
    is_featured = models.BooleanField("Show on home page", default=False)
    order = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=10, choices=PublishStatus.choices, default=PublishStatus.DRAFT)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["order", "price_per_night"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("rooms:detail", args=[self.slug])

    @property
    def cover_url(self):
        first = self.images.first()
        return first.image_url if first and first.image_url else PLACEHOLDER


class RoomImage(models.Model):
    room = models.ForeignKey(Room, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="rooms/", blank=True)
    external_url = models.URLField("Or image link", max_length=500, blank=True)
    alt_text = models.CharField(max_length=160, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    @property
    def image_url(self):
        return self.image.url if self.image else self.external_url