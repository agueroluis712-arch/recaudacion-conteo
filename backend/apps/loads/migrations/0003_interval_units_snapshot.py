from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("loads", "0002_progression_snapshot"), ("progression", "0002_interval_units")]
    operations = [
        migrations.RenameField(model_name="revenueload", old_name="interval_minutes_snapshot", new_name="interval_value_snapshot"),
        migrations.AddField(model_name="revenueload", name="interval_unit_snapshot", field=models.CharField(default="MINUTES", max_length=10)),
    ]
