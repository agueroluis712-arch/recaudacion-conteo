from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.catalogs.models import CollectionChannel
from .services import rows_from_workbook


class RevenueLoadApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("admin-test", password="UnaClaveSegura-2026")
        self.client.force_login(self.user)

    def payload(self):
        channel = CollectionChannel.objects.first()
        return {
            "revenue_date": timezone.localdate().isoformat(),
            "tgp_entry_date": timezone.localdate().isoformat(),
            "channel_id": channel.id,
            "cutoff_time": "23:59",
            "publication_delay_minutes": 30,
            "rows": [{
                "code": "INM", "receipt_count": 4, "gross": "1000.00",
                "commission": "50.00", "vat": "10.50", "other_expenses": "7.00",
            }],
        }

    def test_creates_load_and_calculates_net_without_other_expenses(self):
        response = self.client.post(reverse("loads"), self.payload(), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["gross_total"], "1000.00")
        self.assertEqual(response.json()["net_total"], "939.50")
        self.assertEqual(response.json()["receipt_count"], 4)

    def test_rejects_exact_duplicate(self):
        self.client.post(reverse("loads"), self.payload(), content_type="application/json")
        response = self.client.post(reverse("loads"), self.payload(), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("exactamente", response.json()["error"])

    def test_rounds_excel_decimal_residue_to_two_decimals(self):
        payload = self.payload()
        payload["rows"][0]["gross"] = "10.4999999998"
        response = self.client.post(reverse("loads"), payload, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["gross_total"], "10.50")

    def test_rejects_negative_money(self):
        payload = self.payload()
        payload["rows"][0]["commission"] = "-0.01"
        response = self.client.post(reverse("loads"), payload, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("no puede ser negativo", response.json()["error"])

    def test_accepts_argentine_currency_copied_from_excel(self):
        payload = self.payload()
        payload["rows"][0].update({"gross": "$61.011.456,23", "commission": "$790.511,30", "vat": "$162.511,43"})
        response = self.client.post(reverse("loads"), payload, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["gross_total"], "61011456.23")
        self.assertEqual(response.json()["net_total"], "60058433.50")

    def test_public_counter_returns_only_gross_and_public_metadata(self):
        created = self.client.post(reverse("loads"), self.payload(), content_type="application/json")
        self.assertEqual(created.status_code, 201)
        self.client.logout()
        response = self.client.get(reverse("public-counter"))
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("gross_visible", body)
        self.assertNotIn("net_total", body)
        self.assertNotIn("receipt_count", body)

    def test_official_workbook_reads_only_the_15_detail_rows(self):
        path = settings.BASE_DIR.parent / "templates" / "plantilla-carga-recaudacion.xlsx"
        with path.open("rb") as workbook:
            rows = rows_from_workbook(workbook)
        self.assertEqual(len(rows), 15)
        self.assertEqual(rows[0]["code"], "INM")
        self.assertEqual(rows[-1]["code"], "OTROS")
