from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase, override_settings
from django.urls import reverse


class AuthenticationAndRolesTests(TestCase):
    @override_settings(DEBUG=True)
    def test_local_bootstrap_creates_only_the_first_administrator(self):
        secure_client = Client(enforce_csrf_checks=True)
        csrf_response = secure_client.get(reverse("auth-csrf"))
        self.assertEqual(csrf_response.status_code, 200)
        token = csrf_response.cookies["csrftoken"].value
        response = secure_client.post(
            reverse("auth-bootstrap"),
            {
                "username": "administrador",
                "password": "ClaveInicialSegura-2026",
                "first_name": "Luis",
                "last_name": "Administrador",
            },
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(username="administrador")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.groups.filter(name="ADMINISTRADOR").exists())
        second = secure_client.post(
            reverse("auth-bootstrap"),
            {"username": "otro", "password": "OtraClaveSegura-2026"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(second.status_code, 403)

    def test_internal_endpoints_require_authentication(self):
        self.assertEqual(self.client.get(reverse("catalogs")).status_code, 403)
        self.assertEqual(self.client.get(reverse("loads")).status_code, 403)
        self.assertEqual(self.client.get(reverse("progression-settings")).status_code, 403)
        self.assertEqual(self.client.get(reverse("public-counter")).status_code, 200)

    def test_seeded_roles_have_expected_permissions(self):
        operator = Group.objects.get(name="OPERADOR")
        supervisor = Group.objects.get(name="SUPERVISOR")
        administrator = Group.objects.get(name="ADMINISTRADOR")
        self.assertTrue(operator.permissions.filter(codename="add_revenueload").exists())
        self.assertFalse(operator.permissions.filter(codename="change_progressionsettings").exists())
        self.assertTrue(supervisor.permissions.filter(codename="approve_revenueload").exists())
        self.assertTrue(administrator.permissions.filter(codename="add_user").exists())

    def test_administrator_can_create_operator(self):
        User = get_user_model()
        admin = User.objects.create_superuser("admin-test", password="UnaClaveSegura-2026")
        self.client.force_login(admin)
        response = self.client.post(
            reverse("users"),
            {
                "username": "operador1",
                "password": "OtraClaveSegura-2026",
                "first_name": "Ana",
                "last_name": "Pérez",
                "role": "OPERADOR",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        created = User.objects.get(username="operador1")
        self.assertTrue(created.groups.filter(name="OPERADOR").exists())

    def test_operator_cannot_manage_users_or_configuration(self):
        User = get_user_model()
        operator = User.objects.create_user("operador-test", password="UnaClaveSegura-2026")
        operator.groups.add(Group.objects.get(name="OPERADOR"))
        self.client.force_login(operator)
        self.assertEqual(self.client.get(reverse("users")).status_code, 403)
        self.assertEqual(
            self.client.patch(reverse("progression-settings"), {"interval_value": 3}, content_type="application/json").status_code,
            403,
        )
