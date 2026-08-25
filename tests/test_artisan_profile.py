import unittest
from unittest import mock

from main import app, normalize_artisan_record


class CustomerProfileRenderTests(unittest.TestCase):
    def test_profile_route_matches_signed_up_customer_account(self):
        client = app.test_client()
        with client.session_transaction() as session:
            session["customer_email"] = "jane@example.com"

        with mock.patch("main.requests.get") as mocked_get:
            mocked_get.return_value.raise_for_status.return_value = None
            mocked_get.return_value.json.return_value = {
                "user_123": {
                    "name": "Jane",
                    "surname": "Smith",
                    "email": "jane@example.com",
                    "bookings": 8,
                    "active": 2,
                    "spent": 1800,
                    "current_order": {
                        "artisan_name": "Lerato Fix",
                        "artisan_role": "Plumber",
                        "status": "Completed",
                        "desc": "Replaced the leaking pipe and tested the new connection.",
                    },
                }
            }

            response = client.get("/profile")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Jane Smith", html)
        self.assertIn("jane@example.com", html)
        self.assertIn("Lerato Fix", html)
        self.assertNotIn("Preneil Naidoo", html)


class ArtisanProfileNormalizationTests(unittest.TestCase):
    def test_maps_real_artisan_fields(self):
        artisan = normalize_artisan_record(
            "-N123",
            {
                "name": "Jane Smith",
                "profession": "Electrician",
                "email": "jane@example.com",
                "qualification": "Wireman",
                "hourlyRate": "650",
                "calloutFee": "300",
                "available": True,
                "verified": True,
            },
        )

        self.assertEqual(artisan["id"], "-N123")
        self.assertEqual(artisan["name"], "Jane Smith")
        self.assertEqual(artisan["category"], "electrician")
        self.assertEqual(artisan["rate"], 650)
        self.assertEqual(artisan["calloutFee"], 300)
        self.assertTrue(artisan["available"])

    def test_defaults_missing_values(self):
        artisan = normalize_artisan_record("-N456", {"name": "Plumber One"})
        self.assertEqual(artisan["category"], "repair")
        self.assertEqual(artisan["hourlyRate"], 550)
        self.assertEqual(artisan["calloutFee"], 250)

    def test_feed_route_keeps_artisan_in_artisan_flow(self):
        client = app.test_client()
        with client.session_transaction() as session:
            session["role"] = "artisan"
            session["artisan_id"] = "artisan-123"

        response = client.get("/feed")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/artisan/artisan-123")


if __name__ == "__main__":
    unittest.main()
