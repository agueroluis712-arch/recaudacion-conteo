from django.urls import path

from .views import catalogs

urlpatterns = [path("catalogs/", catalogs, name="catalogs")]
