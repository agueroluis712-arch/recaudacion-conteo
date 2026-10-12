from django.db import migrations


CONCEPTS = [
    ("INM", "INMOBILIARIO", "INMOBILIARIO"),
    ("AUT", "AUTOMOTOR", "AUTOMOTOR"),
    ("IIBB_LOC", "II.BB (Local)", "INGRESOS_BRUTOS"),
    ("IIBB_RS", "II.BB. (Reg. Simplificado)", "INGRESOS_BRUTOS"),
    ("IIBB_RET", "II.BB. (Retención)", "INGRESOS_BRUTOS"),
    ("IIBB_PER", "II.BB. (Percepción)", "INGRESOS_BRUTOS"),
    ("IIBB_RET_CM", "II.BB. (RET. C.M.)", "INGRESOS_BRUTOS"),
    ("IIBB_PER_CM", "II.BB. (PERCEP. C.M.)", "INGRESOS_BRUTOS"),
    ("IIBB_CM", "II.BB. (Conv. Multil.)", "INGRESOS_BRUTOS"),
    ("IIBB_ARB", "II.BB. (Ag.Rec.B.)", "INGRESOS_BRUTOS"),
    ("IIBB_SIRCREB", "II.BB. (Sircreb)", "INGRESOS_BRUTOS"),
    ("SEL", "SELLOS", "SELLOS"),
    ("AG_SEL", "AG. DE SELLOS", "SELLOS"),
    ("TRS", "TASA RETRIBUTIVA", "SELLOS"),
    ("OTROS", "Otros", "OTROS"),
]


def seed(apps, schema_editor):
    Concept = apps.get_model("catalogs", "RevenueConcept")
    Channel = apps.get_model("catalogs", "CollectionChannel")
    for index, (code, name, group) in enumerate(CONCEPTS, start=1):
        Concept.objects.update_or_create(code=code, defaults={
            "name": name, "group": group, "display_order": index * 10, "active": True,
        })
    for name in ("Carga manual", "Transferencia bancaria", "Débito automático", "Otros"):
        Channel.objects.get_or_create(name=name)


def unseed(apps, schema_editor):
    apps.get_model("catalogs", "RevenueConcept").objects.filter(code__in=[c[0] for c in CONCEPTS]).delete()


class Migration(migrations.Migration):
    dependencies = [("catalogs", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
