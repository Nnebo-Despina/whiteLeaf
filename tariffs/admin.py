from django.contrib import admin

from .models import TariffItem, TariffSection


class TariffItemInline(admin.TabularInline):
    model = TariffItem
    extra = 1


@admin.register(TariffSection)
class TariffSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [TariffItemInline]