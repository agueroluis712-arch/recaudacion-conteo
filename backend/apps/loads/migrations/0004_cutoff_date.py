import django.utils.timezone
from django.db import migrations, models


def use_tgp_date(apps, schema_editor):
    Load = apps.get_model("loads", "RevenueLoad")
    for item in Load.objects.all().only("id", "tgp_entry_date"):
        item.cutoff_date = item.tgp_entry_date
        item.save(update_fields=["cutoff_date"])


class Migration(migrations.Migration):
    dependencies = [("loads", "0003_interval_units_snapshot")]
    operations = [
        migrations.AddField(model_name="revenueload", name="cutoff_date", field=models.DateField(default=django.utils.timezone.localdate)),
        migrations.RunPython(use_tgp_date, migrations.RunPython.noop),
    ]
