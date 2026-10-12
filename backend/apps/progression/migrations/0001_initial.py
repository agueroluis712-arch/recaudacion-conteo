from decimal import Decimal
from django.db import migrations, models
import django.core.validators


def seed(apps, schema_editor):
    apps.get_model("progression", "ProgressionSettings").objects.get_or_create(pk=1)


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="ProgressionSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("algorithm", models.CharField(choices=[("LINEAL_ALEATORIO_CONTROLADO", "Lineal aleatorio controlado"), ("LINEAL", "Lineal"), ("ACELERADO_AL_FINAL", "Acelerado al final"), ("INMEDIATO", "Inmediato")], default="LINEAL_ALEATORIO_CONTROLADO", max_length=40)),
                ("publication_delay_minutes", models.PositiveIntegerField(default=30, validators=[django.core.validators.MaxValueValidator(1440)])),
                ("interval_minutes", models.PositiveIntegerField(default=5, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(1440)])),
                ("max_variation_percent", models.DecimalField(decimal_places=2, default=Decimal("20.00"), max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ("randomness_intensity_percent", models.DecimalField(decimal_places=2, default=Decimal("70.00"), max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ("smoothing_intervals", models.PositiveIntegerField(default=5, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ("tv_animation_seconds", models.PositiveIntegerField(default=5, validators=[django.core.validators.MaxValueValidator(60)])),
                ("gamma", models.DecimalField(decimal_places=2, default=Decimal("2.00"), max_digits=4, validators=[django.core.validators.MinValueValidator(Decimal("0.10")), django.core.validators.MaxValueValidator(Decimal("10.00"))])),
                ("counter_gross_only", models.BooleanField(default=True)),
                ("show_group_breakdown", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
