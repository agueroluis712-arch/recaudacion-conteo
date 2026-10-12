import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("progression", "0002_interval_units")]
    operations = [
        migrations.AddField(model_name="progressionsettings", name="display_period", field=models.CharField(choices=[("DAILY", "Día determinado"), ("MONTHLY", "Acumulado mensual"), ("ANNUAL", "Acumulado anual")], default="DAILY", max_length=10)),
        migrations.AddField(model_name="progressionsettings", name="reference_date", field=models.DateField(default=django.utils.timezone.localdate)),
    ]
