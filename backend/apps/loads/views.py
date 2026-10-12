import json

from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.users.permissions import HasLoadAccess
from .models import RevenueLoad
from .services import create_load, rows_from_workbook, serialize_load


@api_view(["GET", "POST"])
@permission_classes([HasLoadAccess])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def loads(request):
    if request.method == "GET":
        queryset = RevenueLoad.objects.select_related("channel").prefetch_related("lines")[:100]
        return Response([serialize_load(item) for item in queryset])
    try:
        upload = request.FILES.get("file")
        if upload:
            payload = request.data
            rows = rows_from_workbook(upload)
            source_name = upload.name
        else:
            payload = request.data
            rows = payload.get("rows", [])
            if isinstance(rows, str):
                rows = json.loads(rows)
            source_name = "Pegado en pantalla"
        item = create_load(payload, rows, source_name)
        return Response(serialize_load(item, include_lines=True), status=201)
    except (ValueError, json.JSONDecodeError) as exc:
        return Response({"error": str(exc)}, status=400)


@api_view(["GET"])
@permission_classes([HasLoadAccess])
def load_detail(request, load_id):
    item = RevenueLoad.objects.select_related("channel").prefetch_related("lines__concept").filter(pk=load_id).first()
    if not item:
        return Response({"error": "Carga no encontrada"}, status=404)
    return Response(serialize_load(item, include_lines=True))
