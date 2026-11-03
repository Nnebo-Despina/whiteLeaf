from django.db import models

from core.models import TimeStamped


class BookingRequest(TimeStamped):
    """A booking request sent from the website (or added by staff for a phone / walk-in booking)."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    check_in = models.DateField()
    check_out = models.DateField()
    adults = models.PositiveSmallIntegerField(default=1)
    children = models.PositiveSmallIntegerField(default=0)
    room = models.ForeignKey("rooms.Room", null=True, blank=True, on_delete=models.SET_NULL, related_name="booking_requests")
    room_label = models.CharField(max_length=120, blank=True, help_text="Filled in for you from the room chosen")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW, db_index=True)
    admin_note = models.TextField("Staff note", blank=True, help_text="Only you can see this.")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "booking request"

    def __str__(self):
        return f"{self.reference} · {self.name}"

    def save(self, *args, **kwargs):
        if self.room_id and not self.room_label:
            self.room_label = self.room.name
        if not self.room_id and not self.room_label:
            self.room_label = "Any available room"
        super().save(*args, **kwargs)

    @property
    def reference(self):
        return f"WL-{self.pk:05d}" if self.pk else "WL-new"

    @property
    def nights(self):
        return max((self.check_out - self.check_in).days, 0)
