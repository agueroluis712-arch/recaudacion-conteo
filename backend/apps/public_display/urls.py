from django.urls import path

from .views import public_counter

urlpatterns = [path("public/counter/", public_counter, name="public-counter")]
