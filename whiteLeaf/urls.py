"""
URL configuration for whiteLeaf project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.contrib.sitemaps.views import sitemap
from core.sitemaps import sitemaps
from core.views import robots_txt
from django.views.generic import RedirectView
from django.conf.urls.static import static as media_static
from django.templatetags.static import static as static_url

urlpatterns = [
    path("manage/", include("cms.urls")),
    path("backstage-x7k2/", admin.site.urls),
    path("accommodations/", include("rooms.urls")),
    path("tariffs/", include("tariffs.urls")),
    path("reviews/", include("reviews.urls")),
    path("", include("core.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", robots_txt, name="robots"),
    path("favicon.ico", RedirectView.as_view(url=static_url("images/favicon.png"), permanent=True)),
]

if settings.DEBUG:
    urlpatterns += media_static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)