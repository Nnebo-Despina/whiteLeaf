from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("display_name", "rating", "status", "is_featured", "created_at")
    list_filter = ("status", "rating")
    actions = ["approve", "reject"]

    @admin.action(description="Approve selected reviews")
    def approve(self, request, queryset):
        queryset.update(status=Review.Status.APPROVED)

    @admin.action(description="Reject selected reviews")
    def reject(self, request, queryset):
        queryset.update(status=Review.Status.REJECTED)