import unittest
import sys
import types
from unittest.mock import patch

fake_requests = types.SimpleNamespace()
fake_requests.exceptions = types.SimpleNamespace(
    Timeout=TimeoutError,
    HTTPError=Exception,
    RequestException=Exception,
)
fake_requests.get = None
sys.modules.setdefault("requests", fake_requests)

from utils import scraper


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise scraper.requests.exceptions.HTTPError(response=self)


class ScraperTests(unittest.TestCase):
    def test_collection_mode_detection_requires_ecommerce_and_collection_page_type(self):
        self.assertTrue(scraper.is_ecommerce_collection_page("ecommerce", "category"))
        self.assertTrue(scraper.is_ecommerce_collection_page("Ecommerce", "Collection Page"))
        self.assertFalse(scraper.is_ecommerce_collection_page("ecommerce", "product"))
        self.assertFalse(scraper.is_ecommerce_collection_page("b2b", "category"))

    def test_default_scraper_still_filters_price_only_product_listing_noise(self):
        html = """
Title: Category Page

## [Blue Runner Shoe](https://example.com/products/blue-runner)

$49.99

This collection has lightweight shoes for everyday training and weekend runs.
"""
        with patch.object(scraper.requests, "get", return_value=FakeResponse(html)):
            result = scraper.scrape_page_context("", "https://example.com/collections/shoes")

        self.assertTrue(result["success"])
        self.assertNotIn("Blue Runner Shoe", result["content"])
        self.assertNotIn("$49.99", result["content"])
        self.assertIn("lightweight shoes", result["content"])

    def test_collection_scraper_keeps_product_prices_and_filters_without_global_noise(self):
        html = """
Title: Running Shoes

Menu

Filters
Brand
Nike
Adidas
Size
8
9
10

## [Blue Runner Shoe](https://example.com/products/blue-runner)
$49.99

## [Trail Grip Shoe](https://example.com/products/trail-grip)
Sale price
$69.00

Add to cart
Footer
This collection has lightweight shoes for road running and trail workouts.
"""
        with patch.object(scraper.requests, "get", return_value=FakeResponse(html)):
            result = scraper.scrape_page_context(
                "",
                "https://example.com/collections/shoes",
                mode="ecommerce_collection",
            )

        self.assertTrue(result["success"])
        self.assertIn("COLLECTION CONTEXT", result["content"])
        self.assertIn("Blue Runner Shoe | $49.99", result["content"])
        self.assertIn("Trail Grip Shoe | $69.00", result["content"])
        self.assertIn("Brand: Nike, Adidas", result["content"])
        self.assertIn("Size: 8, 9, 10", result["content"])
        self.assertNotIn("Add to cart", result["content"])
        self.assertNotIn("Menu", result["content"])


if __name__ == "__main__":
    unittest.main()
