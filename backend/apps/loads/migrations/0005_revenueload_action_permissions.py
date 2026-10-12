from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("loads", "0004_cutoff_date")]

    operations = [
        migrations.AlterModelOptions(
            name="revenueload",
            options={
                "ordering": ("-uploaded_at",),
                "permissions": (
                    ("approve_revenueload", "Puede aprobar cargas de recaudación"),
                    ("annul_revenueload", "Puede anular cargas de recaudación"),
                    ("replace_revenueload", "Puede reemplazar cargas de recaudación"),
                ),
            },
        ),
    ]
