from django.db import migrations


ROLE_PERMISSIONS = {
    "OPERADOR": {
        "catalogs.view_collectionchannel",
        "catalogs.view_revenueconcept",
        "loads.view_revenueload",
        "loads.add_revenueload",
        "loads.view_revenueline",
        "loads.add_revenueline",
        "progression.view_progressionsettings",
    },
    "SUPERVISOR": {
        "catalogs.view_collectionchannel",
        "catalogs.view_revenueconcept",
        "loads.view_revenueload",
        "loads.add_revenueload",
        "loads.change_revenueload",
        "loads.view_revenueline",
        "loads.add_revenueline",
        "loads.change_revenueline",
        "loads.approve_revenueload",
        "loads.annul_revenueload",
        "loads.replace_revenueload",
        "progression.view_progressionsettings",
        "progression.change_progressionsettings",
    },
    "ADMINISTRADOR": {
        "auth.view_user", "auth.add_user", "auth.change_user",
        "auth.view_group", "auth.add_group", "auth.change_group",
        "catalogs.view_collectionchannel", "catalogs.add_collectionchannel", "catalogs.change_collectionchannel",
        "catalogs.view_revenueconcept", "catalogs.add_revenueconcept", "catalogs.change_revenueconcept",
        "loads.view_revenueload", "loads.add_revenueload", "loads.change_revenueload",
        "loads.view_revenueline", "loads.add_revenueline", "loads.change_revenueline",
        "loads.approve_revenueload", "loads.annul_revenueload", "loads.replace_revenueload",
        "progression.view_progressionsettings", "progression.change_progressionsettings",
    },
}


def seed_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    model_names = {
        "auth": ("user", "group"),
        "catalogs": ("collectionchannel", "revenueconcept"),
        "loads": ("revenueload", "revenueline"),
        "progression": ("progressionsettings",),
    }
    custom_names = {
        "approve_revenueload": "Puede aprobar cargas de recaudación",
        "annul_revenueload": "Puede anular cargas de recaudación",
        "replace_revenueload": "Puede reemplazar cargas de recaudación",
    }
    for app_label, models in model_names.items():
        for model in models:
            content_type, _ = ContentType.objects.get_or_create(app_label=app_label, model=model)
            for action in ("add", "change", "delete", "view"):
                Permission.objects.get_or_create(
                    content_type=content_type,
                    codename=f"{action}_{model}",
                    defaults={"name": f"Can {action} {model}"},
                )
            if model == "revenueload":
                for codename, name in custom_names.items():
                    Permission.objects.get_or_create(content_type=content_type, codename=codename, defaults={"name": name})

    for role_name, permission_labels in ROLE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=role_name)
        permissions = []
        for label in permission_labels:
            app_label, codename = label.split(".", 1)
            permissions.append(Permission.objects.get(content_type__app_label=app_label, codename=codename))
        group.permissions.set(permissions)


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("catalogs", "0002_seed_catalogs"),
        ("loads", "0005_revenueload_action_permissions"),
        ("progression", "0006_expand_tv_animation_seconds"),
    ]

    operations = [migrations.RunPython(seed_roles, migrations.RunPython.noop)]
