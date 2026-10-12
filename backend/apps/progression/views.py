from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.users.permissions import HasProgressionAccess
from .models import ProgressionSettings


def serialize(settings):
    return {
        "algorithm": settings.algorithm,
        "publication_delay_minutes": settings.publication_delay_minutes,
        "interval_value": settings.interval_value,
        "interval_unit": settings.interval_unit,
        "display_period": settings.display_period,
        "reference_date": settings.reference_date,
        "max_variation_percent": f"{settings.max_variation_percent:.2f}",
        "randomness_intensity_percent": f"{settings.randomness_intensity_percent:.2f}",
        "smoothing_intervals": settings.smoothing_intervals,
        "tv_animation_seconds": settings.tv_animation_seconds,
        "animation_style": settings.animation_style,
        "adaptive_animation": settings.adaptive_animation,
        "gamma": f"{settings.gamma:.2f}",
        "counter_gross_only": settings.counter_gross_only,
        "show_group_breakdown": settings.show_group_breakdown,
        "updated_at": settings.updated_at,
    }


@api_view(["GET", "PATCH"])
@permission_classes([HasProgressionAccess])
def progression_settings(request):
    settings = ProgressionSettings.get_solo()
    if request.method == "GET":
        return Response(serialize(settings))
    allowed = {
        "algorithm", "publication_delay_minutes", "interval_value", "interval_unit",
        "display_period", "reference_date",
        "max_variation_percent", "randomness_intensity_percent", "smoothing_intervals",
        "tv_animation_seconds", "animation_style", "adaptive_animation", "gamma", "counter_gross_only", "show_group_breakdown",
    }
    try:
        for field, value in request.data.items():
            if field not in allowed:
                continue
            if field in {"counter_gross_only", "show_group_breakdown", "adaptive_animation"}:
                if not isinstance(value, bool):
                    raise ValueError(f"{field}: debe ser verdadero o falso")
                setattr(settings, field, value)
            elif field in {"max_variation_percent", "randomness_intensity_percent", "gamma"}:
                setattr(settings, field, Decimal(str(value)))
            elif field in {"algorithm", "interval_unit", "display_period", "animation_style"}:
                setattr(settings, field, str(value))
            elif field == "reference_date":
                setattr(settings, field, datetime.strptime(str(value), "%Y-%m-%d").date())
            else:
                setattr(settings, field, int(value))
        settings.full_clean()
        if settings.interval_seconds > 86400:
            raise ValueError("El intervalo no puede superar 24 horas")
        settings.save()
    except (ValueError, InvalidOperation, ValidationError) as exc:
        message = exc.message_dict if isinstance(exc, ValidationError) and hasattr(exc, "message_dict") else str(exc)
        return Response({"error": message}, status=400)
    return Response(serialize(settings))
