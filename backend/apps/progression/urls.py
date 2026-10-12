from django.urls import path

from .views import progression_settings

urlpatterns = [path("settings/progression/", progression_settings, name="progression-settings")]
