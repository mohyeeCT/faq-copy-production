import unittest

from utils.page_types import normalize_page_type


class PageTypeNormalizationTests(unittest.TestCase):
    def test_normalizes_supported_page_type_aliases(self):
        cases = {
            "product page": "product",
            "Collection Page": "category",
            "ecommerce category": "category",
            "service_lp": "service",
            "Service Landing Page": "service",
            "LP": "landing_page",
            "location page": "local",
            "city page": "local",
            "blog page": "blog",
            "": "general",
        }

        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(normalize_page_type(value), expected)


if __name__ == "__main__":
    unittest.main()
