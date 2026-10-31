from django.urls import path

from . import views

urlpatterns = [path("", views.tariffs, name="tariffs")]
