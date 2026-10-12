from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.loads.models import RevenueLoad
from apps.progression.models import ProgressionSettings
from apps.progression.services import progression_fraction


@api_view(["GET"])
@permission_classes([AllowAny])
def public_counter(request):
    now = timezone.now()
    configuration = ProgressionSettings.get_solo()
    loads = RevenueLoad.objects.filter(status="VALID")
    reference = configuration.reference_date
    if configuration.display_period == "MONTHLY":
        loads = loads.filter(revenue_date__year=reference.year, revenue_date__month=reference.month)
        period_label = "Acumulado mensual"
    elif configuration.display_period == "ANNUAL":
        loads = loads.filter(revenue_date__year=reference.year)
        period_label = "Acumulado anual"
    else:
        loads = loads.filter(revenue_date=reference)
        period_label = "Recaudación del día"
    loads = loads.prefetch_related("lines__concept").order_by("revenue_date", "uploaded_at")
    visible = Decimal("0.00")
    final = Decimal("0.00")
    groups = {}
    latest_date = None
    active = False
    for item in loads:
        target = item.gross_total
        final += target
        latest_date = max(latest_date, item.revenue_date) if latest_date else item.revenue_date
        start = item.uploaded_at + timedelta(minutes=item.publication_delay_minutes)
        cutoff_naive = datetime.combine(item.cutoff_date, item.cutoff_time)
        cutoff = timezone.make_aware(cutoff_naive)
        if now < start:
            progress = Decimal("0")
        elif now >= cutoff or cutoff <= start:
            progress = Decimal("1")
        else:
            progress = progression_fraction(item, now, start, cutoff)
            active = True
        visible += (target * progress).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if configuration.show_group_breakdown and not configuration.counter_gross_only:
            for line in item.lines.all():
                group = line.concept.group
                groups[group] = groups.get(group, Decimal("0.00")) + (line.gross * progress).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    response = {
        "gross_visible": f"{visible:.2f}", "revenue_date": latest_date,
        "updated_at": now, "is_progressing": active, "load_count": loads.count(),
        "refresh_seconds": configuration.interval_seconds,
        "animation_seconds": configuration.tv_animation_seconds,
        "animation_style": configuration.animation_style,
        "adaptive_animation": configuration.adaptive_animation,
        "counter_gross_only": configuration.counter_gross_only,
        "show_group_breakdown": configuration.show_group_breakdown,
        "display_period": configuration.display_period,
        "period_label": period_label,
        "reference_date": reference,
    }
    if groups:
        response["groups"] = {key: f"{value:.2f}" for key, value in groups.items()}
    return Response(response)
