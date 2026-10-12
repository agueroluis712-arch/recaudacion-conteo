from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.catalogs.models import CollectionChannel, RevenueConcept


class RevenueLoad(models.Model):
    STATUS_CHOICES = (("VALID", "Válida"), ("REPLACED", "Reemplazada"), ("CANCELLED", "Anulada"))

    revenue_date = models.DateField()
    tgp_entry_date = models.DateField()
    channel = models.ForeignKey(CollectionChannel, on_delete=models.PROTECT)
    cutoff_date = models.DateField(default=timezone.localdate)
    cutoff_time = models.TimeField(default="23:59")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    publication_delay_minutes = models.PositiveIntegerField(default=30)
    algorithm_snapshot = models.CharField(max_length=40, default="LINEAL_ALEATORIO_CONTROLADO")
    interval_value_snapshot = models.PositiveIntegerField(default=5)
    interval_unit_snapshot = models.CharField(max_length=10, default="MINUTES")
    max_variation_snapshot = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("20.00"))
    randomness_intensity_snapshot = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("70.00"))
    smoothing_intervals_snapshot = models.PositiveIntegerField(default=5)
    tv_animation_seconds_snapshot = models.PositiveIntegerField(default=5)
    gamma_snapshot = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("2.00"))
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="VALID")
    source_name = models.CharField(max_length=255, blank=True)
    content_hash = models.CharField(max_length=64, unique=True)
    correction_of = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="corrections"
    )
    correction_note = models.TextField(blank=True)

    class Meta:
        ordering = ("-uploaded_at",)
        permissions = (
            ("approve_revenueload", "Puede aprobar cargas de recaudación"),
            ("annul_revenueload", "Puede anular cargas de recaudación"),
            ("replace_revenueload", "Puede reemplazar cargas de recaudación"),
        )

    @property
    def gross_total(self):
        return sum((line.gross for line in self.lines.all()), Decimal("0.00"))

    @property
    def commission_total(self):
        return sum((line.commission for line in self.lines.all()), Decimal("0.00"))

    @property
    def vat_total(self):
        return sum((line.vat for line in self.lines.all()), Decimal("0.00"))

    @property
    def net_total(self):
        return self.gross_total - self.commission_total - self.vat_total


class RevenueLine(models.Model):
    load = models.ForeignKey(RevenueLoad, on_delete=models.CASCADE, related_name="lines")
    concept = models.ForeignKey(RevenueConcept, on_delete=models.PROTECT)
    receipt_count = models.PositiveIntegerField(default=0)
    gross = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    commission = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    vat = models.DecimalField(max_digits=18, decimal_places=2, validators=[MinValueValidator(0)])
    other_expenses = models.DecimalField(max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    observations = models.CharField(max_length=500, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("load", "concept"), name="unique_load_concept")]
