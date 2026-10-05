from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from tracker import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.dashboard, name="dashboard"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="tracker/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/register/", views.register, name="register"),
    path("", include("tracker.urls")),
]