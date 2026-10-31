from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .forms import StaffAuthenticationForm

app_name = "cms"
urlpatterns = [
    path("login/", LoginView.as_view(
        template_name="cms/login.html",
        authentication_form=StaffAuthenticationForm,
        redirect_authenticated_user=True,
    ), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("hotel/", views.HotelEdit.as_view(), name="hotel"),
    path("<slug:section>/", views.SectionList.as_view(), name="list"),
    path("<slug:section>/new/", views.SectionEdit.as_view(), name="new"),
    path("<slug:section>/<int:pk>/", views.SectionEdit.as_view(), name="edit"),
    path("<slug:section>/<int:pk>/delete/", views.SectionDelete.as_view(), name="delete"),
    path("<slug:section>/<int:pk>/status/", views.SectionStatus.as_view(), name="status"),
]
