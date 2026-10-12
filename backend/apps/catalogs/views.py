from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.users.permissions import HasCatalogAccess
from .models import CollectionChannel, RevenueConcept


@api_view(["GET"])
@permission_classes([HasCatalogAccess])
def catalogs(request):
    concepts = RevenueConcept.objects.filter(active=True).values(
        "code", "name", "group", "display_order"
    )
    channels = CollectionChannel.objects.filter(active=True).values("id", "name")
    return Response({"concepts": list(concepts), "channels": list(channels)})
