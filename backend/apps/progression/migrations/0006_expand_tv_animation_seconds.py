from django.core.validators import MaxValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("progression", "0005_adaptive_animation")]

    operations = [
        migrations.AlterField(
            model_name="progressionsettings",
            name="tv_animation_seconds",
            field=models.PositiveIntegerField(default=5, validators=[MaxValueValidator(86400)]),
        ),
    ]
