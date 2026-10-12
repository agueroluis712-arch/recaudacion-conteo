from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.catalogs.models import CollectionChannel
from apps.loads.models import RevenueLoad


class ProgressionSettingsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("admin-test", password="UnaClaveSegura-2026")
        self.client.force_login(self.user)

    def test_defaults_match_approved_values(self):
        response = self.client.get(reverse("progression-settings"))
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["algorithm"], "LINEAL_ALEATORIO_CONTROLADO")
        self.assertEqual(body["publication_delay_minutes"], 30)
        self.assertEqual(body["interval_value"], 5)
        self.assertEqual(body["interval_unit"], "MINUTES")
        self.assertEqual(body["tv_animation_seconds"], 5)
        self.assertEqual(body["display_period"], "DAILY")
        self.assertEqual(body["animation_style"], "COMBINED")
        self.assertTrue(body["adaptive_animation"])
        self.assertIn("reference_date", body)

    def test_update_is_persisted_and_snapshotted_by_new_load(self):
        updated = self.client.patch(
            reverse("progression-settings"),
            {"algorithm": "LINEAL", "interval_value": 8, "interval_unit": "SECONDS", "publication_delay_minutes": 12},
            content_type="application/json",
        )
        self.assertEqual(updated.status_code, 200)
        channel = CollectionChannel.objects.first()
        response = self.client.post(reverse("loads"), {
            "revenue_date": timezone.localdate().isoformat(), "tgp_entry_date": timezone.localdate().isoformat(),
            "channel_id": channel.id, "cutoff_date": timezone.localdate().isoformat(), "cutoff_time": "23:59", "publication_delay_minutes": 12,
            "rows": [{"code": "INM", "receipt_count": 1, "gross": "100", "commission": "0", "vat": "0", "other_expenses": "0"}],
        }, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        load = RevenueLoad.objects.get(pk=response.json()["id"])
        self.assertEqual(load.algorithm_snapshot, "LINEAL")
        self.assertEqual(load.interval_value_snapshot, 8)
        self.assertEqual(load.interval_unit_snapshot, "SECONDS")
