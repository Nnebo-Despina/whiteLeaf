from django.db import models


class TariffSection(models.Model):
    title = models.CharField("Menu title", max_length=80, help_text="Shown in the table of contents")
    heading = models.CharField(max_length=120, blank=True, help_text="Big heading on the page. Blank = menu title.")
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=40, default="info", help_text="Lucide icon name, e.g. clock, car, users")
    body = models.TextField(
        blank=True,
        help_text="Paragraph(s). Blank line = new paragraph. You can use {phone}, {address}, {check_in}, {check_out}.",
    )
    footnote = models.CharField(max_length=200, blank=True, help_text="Small line under the table")
    show_room_rates = models.BooleanField(default=False, help_text="Fill the table with live room prices")
    show_contact_button = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField("Show on site", default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    @property
    def display_heading(self):
        return self.heading or self.title

    @property
    def paragraphs(self):
        return [p.strip() for p in self.body.split("\n\n") if p.strip()]


class TariffItem(models.Model):
    class PriceType(models.TextChoices):
        FIXED = "fixed", "Fixed amount"
        NIGHT = "night", "Per night"
        DAY = "day", "Per day"
        ITEM = "item", "Per item"
        FREE = "free", "Free"
        TEXT = "text", "Custom text"

    section = models.ForeignKey(TariffSection, related_name="items", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    note = models.CharField(max_length=200, blank=True)
    price_type = models.CharField(max_length=10, choices=PriceType.choices, default=PriceType.FIXED)
    amount = models.DecimalField("Amount (₦)", max_digits=10, decimal_places=2, null=True, blank=True)
    price_text = models.CharField(max_length=60, blank=True, help_text="Only for 'Custom text', e.g. 50% of room rate")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    @property
    def display_price(self):
        if self.price_type == self.PriceType.FREE:
            return "Free"
        if self.price_type == self.PriceType.TEXT:
            return self.price_text
        suffix = {"night": " / night", "day": " / day", "item": " / item"}.get(self.price_type, "")
        return f"₦{(self.amount or 0):,.0f}{suffix}"
