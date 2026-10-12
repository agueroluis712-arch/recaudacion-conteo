from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("progression", "0004_animation_style")]
    operations = [migrations.AddField(model_name="progressionsettings", name="adaptive_animation", field=models.BooleanField(default=True))]
