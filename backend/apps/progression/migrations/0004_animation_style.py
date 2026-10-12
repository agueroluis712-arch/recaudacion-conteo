from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("progression", "0003_display_period")]
    operations = [
        migrations.AddField(model_name="progressionsettings", name="animation_style", field=models.CharField(choices=[("INCREMENTAL", "Contador incremental"), ("ODOMETER", "Odómetro"), ("COMBINED", "Combinado")], default="COMBINED", max_length=12)),
    ]
