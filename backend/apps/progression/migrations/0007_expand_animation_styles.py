from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("progression", "0006_expand_tv_animation_seconds")]

    operations = [
        migrations.AlterField(
            model_name="progressionsettings",
            name="animation_style",
            field=models.CharField(
                choices=[
                    ("INCREMENTAL", "Contador incremental"),
                    ("ODOMETER", "Odómetro"),
                    ("COMBINED", "Combinado"),
                    ("FLIP", "Flip institucional"),
                    ("SLIDE", "Deslizamiento suave"),
                    ("PULSE", "Pulso luminoso"),
                    ("ROLLING", "Rodillo simultáneo"),
                    ("FLUID", "Conteo fluido"),
                ],
                default="COMBINED",
                max_length=12,
            ),
        ),
    ]
