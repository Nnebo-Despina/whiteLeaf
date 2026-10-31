from django.core.validators import MaxLengthValidator, MaxValueValidator, MinLengthValidator, MinValueValidator
from django.db import models

from core.models import TimeStamped


class ReviewQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(status=Review.Status.APPROVED)


class Review(TimeStamped):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    display_name = models.CharField(max_length=80)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    body = models.TextField(validators=[MinLengthValidator(10), MaxLengthValidator(200)])
    stay_note = models.CharField(max_length=120, blank=True, help_text="e.g. Stayed 4 nights, Single Room")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    is_featured = models.BooleanField("Show first", default=False)

    objects = ReviewQuerySet.as_manager()

    class Meta:
        ordering = ["-is_featured", "-created_at"]

    def __str__(self):
        return f"{self.display_name} ({self.rating}★)"