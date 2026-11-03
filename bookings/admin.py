from django.contrib import admin

from .models import BookingRequest


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ("reference", "name", "phone", "check_in", "check_out", "room_label", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "phone")
