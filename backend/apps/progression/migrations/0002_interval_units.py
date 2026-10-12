from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [("progression", "0001_initial")]
    operations = [
        migrations.RenameField(model_name="progressionsettings", old_name="interval_minutes", new_name="interval_value"),
        migrations.AlterField(model_name="progressionsettings", name="interval_value", field=models.PositiveIntegerField(default=5, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(86400)])),
        migrations.AddField(model_name="progressionsettings", name="interval_unit", field=models.CharField(choices=[("SECONDS", "Segundos"), ("MINUTES", "Minutos"), ("HOURS", "Horas")], default="MINUTES", max_length=10)),
    ]
