from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class ProgressionSettings(models.Model):
    ALGORITHMS = (
        ("LINEAL_ALEATORIO_CONTROLADO", "Lineal aleatorio controlado"),
        ("LINEAL", "Lineal"),
        ("ACELERADO_AL_FINAL", "Acelerado al final"),
        ("INMEDIATO", "Inmediato"),
    )
    INTERVAL_UNITS = (("SECONDS", "Segundos"), ("MINUTES", "Minutos"), ("HOURS", "Horas"))
    DISPLAY_PERIODS = (("DAILY", "Día determinado"), ("MONTHLY", "Acumulado mensual"), ("ANNUAL", "Acumulado anual"))
    ANIMATION_STYLES = (
        ("INCREMENTAL", "Contador incremental"),
        ("ODOMETER", "Odómetro"),
        ("COMBINED", "Combinado"),
        ("FLIP", "Flip institucional"),
        ("SLIDE", "Deslizamiento suave"),
        ("PULSE", "Pulso luminoso"),
        ("ROLLING", "Rodillo simultáneo"),
        ("FLUID", "Conteo fluido"),
    )

    algorithm = models.CharField(max_length=40, choices=ALGORITHMS, default="LINEAL_ALEATORIO_CONTROLADO")
    publication_delay_minutes = models.PositiveIntegerField(default=30, validators=[MaxValueValidator(1440)])
    interval_value = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(86400)])
    interval_unit = models.CharField(max_length=10, choices=INTERVAL_UNITS, default="MINUTES")
    display_period = models.CharField(max_length=10, choices=DISPLAY_PERIODS, default="DAILY")
    reference_date = models.DateField(default=timezone.localdate)
    max_variation_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("20.00"), validators=[MinValueValidator(0), MaxValueValidator(100)])
    randomness_intensity_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("70.00"), validators=[MinValueValidator(0), MaxValueValidator(100)])
    smoothing_intervals = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(100)])
    tv_animation_seconds = models.PositiveIntegerField(default=5, validators=[MaxValueValidator(86400)])
    animation_style = models.CharField(max_length=12, choices=ANIMATION_STYLES, default="COMBINED")
    adaptive_animation = models.BooleanField(default=True)
    gamma = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("2.00"), validators=[MinValueValidator(Decimal("0.10")), MaxValueValidator(Decimal("10.00"))])
    counter_gross_only = models.BooleanField(default=True)
    show_group_breakdown = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_solo(cls):
        return cls.objects.get_or_create(pk=1)[0]

    def __str__(self):
        return "Configuración general de progresión"

    @property
    def interval_seconds(self):
        multiplier = {"SECONDS": 1, "MINUTES": 60, "HOURS": 3600}[self.interval_unit]
        return self.interval_value * multiplier
