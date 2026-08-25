import unittest

from main import app, normalize_artisan_record


class CustomerProfileRenderTests(unittest.TestCase):
    def test_profile_route_renders_with_default_user_data(self):
        client = app.test_client()
        response = client.get("/profile")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Pro Fix — My Profile", html)
        self.assertIn("Preneil Naidoo", html)


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


if __name__ == "__main__":
    unittest.main()
