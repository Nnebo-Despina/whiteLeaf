import datetime

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PublishStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"


class HotelInfo(TimeStamped):
    """Exactly one row. Feeds the nav, footer, contact page and tariff text."""

    name = models.CharField(max_length=120, default="White Leaf Hotel & Suites")
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    phone_secondary = models.CharField("Second phone / WhatsApp", max_length=30, blank=True)
    email = models.EmailField(blank=True)
    opening_hours = models.CharField(max_length=80, blank=True, default="Daily: 6am – 10pm")
    check_in_time = models.TimeField(default=datetime.time(14, 0))
    check_out_time = models.TimeField(default=datetime.time(12, 0))
    map_embed_url = models.URLField(
        "Google Maps embed URL", max_length=500, blank=True,
        help_text="Google Maps > Share > Embed a map, then paste the iframe's src. Leave blank to search by address.",
    )
    directions_url = models.URLField("Get directions link", max_length=500, blank=True)

    class Meta:
        verbose_name_plural = "Hotel info"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @classmethod
    def load(cls):
        return cls.objects.first() or cls()


class SiteText(TimeStamped):
    """Editable page copy. `value` is live; `draft_value` is an unpublished edit."""

    key = models.CharField(max_length=60, unique=True)
    label = models.CharField(max_length=120)
    page = models.CharField(max_length=20, blank=True)
    value = models.TextField(blank=True)
    draft_value = models.TextField(blank=True)

    class Meta:
        ordering = ["page", "key"]

    def __str__(self):
        return self.label

    @property
    def has_draft(self):
        return bool(self.draft_value) and self.draft_value != self.value

    def publish(self):
        if self.draft_value:
            self.value, self.draft_value = self.draft_value, ""
        self.save()


class SiteImage(TimeStamped):
    """A photo for one fixed spot on the site.

    Every spot a template fills has its own slot, and the template asks for it by name:
        {% site_image 'contact_cta_1' 'fallback-url' %}
    A section with two photos therefore gets two slots (contact_cta_1, contact_cta_2).
    SLOT_LIMITS below says how many images each slot may hold (default 1).
    """

    class Slot(models.TextChoices):
        HOME_HERO = "home_hero", "Home · hero background"
        HOME_WELCOME = "home_welcome", "Home · welcome photo"
        HOME_VIDEO_POSTER = "home_video_poster", "Home · video cover image"
        HOME_REVIEW = "home_review", "Home · testimonial background"
        HOME_BAR = "home_bar", "Home · bar photo"
        HOME_CTA = "home_cta", "Home · bottom call-to-action"

        TARIFFS_HERO = "tariffs_hero", "Tariffs · hero background"

        ABOUT_HERO = "about_hero", "About · hero background"
        ABOUT_DEDICATED = "about_dedicated", "About · 'Dedicated to serving you' backup photo"
        ABOUT_STAFF = "about_staff", "About · staff section photo"

        CONTACT_CTA_1 = "contact_cta_1", "Contact · call-to-action photo (left)"
        CONTACT_CTA_2 = "contact_cta_2", "Contact · call-to-action photo (right)"

    title = models.CharField(max_length=120)
    slot = models.CharField(max_length=40, choices=Slot.choices)
    image = models.ImageField(upload_to="site/")
    alt_text = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=10, choices=PublishStatus.choices, default=PublishStatus.DRAFT)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.slot:
            taken = SiteImage.objects.filter(slot=self.slot).exclude(pk=self.pk).count()
            limit = slot_limit(self.slot)
            if taken >= limit:
                raise ValidationError({
                    "slot": f"This spot already has its image{'s' if limit > 1 else ''}. "
                            "Edit the existing one instead of adding another."
                })


# How many images each slot can hold. Anything not listed holds 1.
SLOT_LIMITS = {}


def slot_limit(slot):
    return SLOT_LIMITS.get(slot, 1)


MAX_VIDEO_MB = 50


class SiteVideo(TimeStamped):
    """A video for one fixed spot on the site (same one-per-spot rule as SiteImage)."""

    class Slot(models.TextChoices):
        HOME_PROMO = "home_promo", "Home · promo video (hero corner)"

    title = models.CharField(max_length=120)
    slot = models.CharField(max_length=40, choices=Slot.choices)
    video = models.FileField(
        upload_to="videos/",
        validators=[FileExtensionValidator(["mp4", "webm"])],
        help_text=f"MP4 or WebM, up to {MAX_VIDEO_MB} MB. Shorter, compressed clips load faster.",
    )
    status = models.CharField(max_length=10, choices=PublishStatus.choices, default=PublishStatus.DRAFT)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.slot:
            taken = SiteVideo.objects.filter(slot=self.slot).exclude(pk=self.pk).count()
            if taken >= slot_limit(self.slot):
                raise ValidationError({"slot": "This spot already has its video. Edit the existing one instead of adding another."})
        if self.video and not self.video._committed and self.video.size > MAX_VIDEO_MB * 1024 * 1024:
            raise ValidationError({"video": f"That file is too large. Keep it under {MAX_VIDEO_MB} MB."})


class FAQ(TimeStamped):
    question = models.CharField(max_length=200)
    answer = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField("Show on site", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "FAQ"

    def __str__(self):
        return self.question


class Facility(TimeStamped):
    """Home page 'Hotel amenities' grid."""

    title = models.CharField(max_length=60)
    icon = models.CharField(max_length=40, help_text="Lucide icon name, e.g. wifi, waves, dumbbell, coffee")
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField("Show on site", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name_plural = "Facilities"

    def __str__(self):
        return self.title


class Attraction(TimeStamped):
    """Home page 'Nearby, worth the walk' cards."""

    name = models.CharField(max_length=80)
    image = models.ImageField(upload_to="nearby/", blank=True)
    external_url = models.URLField("Or image link", max_length=500, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField("Show on site", default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name

    @property
    def image_url(self):
        return self.image.url if self.image else self.external_url


class Feature(TimeStamped):
    """About page: the four rotating feature columns. Each one also drives the photo and caption above them."""

    title = models.CharField(max_length=60)
    description = models.CharField(max_length=220)
    caption = models.CharField(
        max_length=160, blank=True,
        help_text="Text shown over the photo while this feature is highlighted. Blank = the general caption.",
    )
    image = models.ImageField(upload_to="feature/", blank=True)
    external_url = models.URLField("Or image link", max_length=500, blank=True)
    tint = models.CharField(max_length=7, default="#1f5d45", help_text="Hex colour, e.g. #1f5d45")
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField("Show on site", default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    @property
    def image_url(self):
        return self.image.url if self.image else self.external_url