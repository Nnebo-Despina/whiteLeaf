from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("manage/", include("cms.urls")),            # your dashboard
    path("backstage-x7k2/", admin.site.urls),        # Django's built-in admin: change this to your own random string
    path("accommodations/", include("rooms.urls")),
    path("tariffs/", include("tariffs.urls")),
    path("reviews/", include("reviews.urls")),
    path("", include("core.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
