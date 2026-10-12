from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.http import FileResponse, JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    return JsonResponse({"status": "ok", "service": "recaudacion-api"})


@require_GET
@login_required
@permission_required("loads.add_revenueload", raise_exception=True)
def excel_template(request):
    path = settings.BASE_DIR.parent / "templates" / "plantilla-carga-recaudacion.xlsx"
    return FileResponse(path.open("rb"), as_attachment=True, filename="plantilla-carga-recaudacion.xlsx")
