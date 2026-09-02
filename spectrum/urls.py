"""
URL configuration for spectrum project.
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from agent_portal.views import SpectrumLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", SpectrumLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("agent_portal.urls")),
]
