from django.contrib import admin

from .models import FAQ, Attraction, Facility, Feature, HotelInfo, SiteImage, SiteText

for m in (HotelInfo, SiteText, SiteImage, FAQ, Facility, Attraction, Feature):
    admin.site.register(m)