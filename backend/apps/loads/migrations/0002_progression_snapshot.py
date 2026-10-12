from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("loads", "0001_initial"), ("progression", "0001_initial")]
    operations = [
        migrations.AddField(model_name="revenueload", name="algorithm_snapshot", field=models.CharField(default="LINEAL_ALEATORIO_CONTROLADO", max_length=40)),
        migrations.AddField(model_name="revenueload", name="interval_minutes_snapshot", field=models.PositiveIntegerField(default=5)),
        migrations.AddField(model_name="revenueload", name="max_variation_snapshot", field=models.DecimalField(decimal_places=2, default=Decimal("20.00"), max_digits=5)),
        migrations.AddField(model_name="revenueload", name="randomness_intensity_snapshot", field=models.DecimalField(decimal_places=2, default=Decimal("70.00"), max_digits=5)),
        migrations.AddField(model_name="revenueload", name="smoothing_intervals_snapshot", field=models.PositiveIntegerField(default=5)),
        migrations.AddField(model_name="revenueload", name="tv_animation_seconds_snapshot", field=models.PositiveIntegerField(default=5)),
        migrations.AddField(model_name="revenueload", name="gamma_snapshot", field=models.DecimalField(decimal_places=2, default=Decimal("2.00"), max_digits=4)),
    ]
