from django.urls import path
from . import views

app_name = "reviews"
urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("submit/", views.submit_review, name="submit")
]
