from django.urls import path

from .views import excel_template, health


urlpatterns = [
    path("health/", health, name="health"),
    path("template/", excel_template, name="excel-template"),
]
