import unittest

from main import normalize_artisan_record


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
