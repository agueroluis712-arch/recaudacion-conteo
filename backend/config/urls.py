from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.common.urls")),
    path("api/", include("apps.catalogs.urls")),
    path("api/", include("apps.loads.urls")),
    path("api/", include("apps.progression.urls")),
    path("api/", include("apps.public_display.urls")),
]
