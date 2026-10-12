from django.urls import path

from .views import load_detail, loads

urlpatterns = [
    path("loads/", loads, name="loads"),
    path("loads/<int:load_id>/", load_detail, name="load-detail"),
]
