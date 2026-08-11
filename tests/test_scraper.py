import unittest
import sys
import types
from unittest.mock import patch


class FakeHTTPError(Exception):
    def __init__(self, response=None):
        super().__init__()
        self.response = response


fake_requests = types.SimpleNamespace()
fake_requests.exceptions = types.SimpleNamespace(
    Timeout=TimeoutError,
    HTTPError=FakeHTTPError,
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
    def test_scraper_retries_transient_503_then_returns_content(self):
        html = """
Title: Balloon Collection

This collection includes colorful balloons for birthdays, weddings, graduations, and other celebrations.
"""
        with (
            patch.object(
                scraper.requests,
                "get",
                side_effect=[FakeResponse("", 503), FakeResponse(html)],
            ) as request,
            patch("time.sleep") as sleep,
        ):
            result = scraper.scrape_page_context(
                "",
                "https://example.com/collections/balloons",
            )

        self.assertTrue(result["success"])
        self.assertIn("colorful balloons", result["content"])
        self.assertEqual(request.call_count, 2)
        sleep.assert_called_once()
        self.assertNotIn(
            "X-Remove-Selector",
            request.call_args_list[1].kwargs["headers"],
        )
        self.assertEqual(request.call_args.kwargs["timeout"], 55)
        self.assertEqual(request.call_args.kwargs["headers"]["X-Timeout"], "45")

    def test_scraper_stops_after_transient_retry_limit(self):
        with (
            patch.object(
                scraper.requests,
                "get",
                side_effect=[
                    FakeResponse("", 503),
                    FakeResponse("", 503),
                ],
            ) as request,
            patch("time.sleep") as sleep,
        ):
            result = scraper.scrape_page_context(
                "",
                "https://example.com/collections/balloons",
            )

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "HTTP 503")
        self.assertEqual(request.call_count, 2)
        self.assertEqual(
            [sleep_call.args[0] for sleep_call in sleep.call_args_list],
            [2.0],
        )

    def test_scraper_retries_timeout_once_without_selector(self):
        html = """
Title: Balloon Collection

This collection includes colorful balloons for birthdays, weddings, graduations, and other celebrations.
"""
        with patch.object(
            scraper.requests,
            "get",
            side_effect=[scraper.requests.exceptions.Timeout(), FakeResponse(html)],
        ) as request:
            result = scraper.scrape_page_context(
                "",
                "https://example.com/collections/balloons",
            )

        self.assertTrue(result["success"])
        self.assertEqual(request.call_count, 2)
        self.assertNotIn(
            "X-Remove-Selector",
            request.call_args_list[1].kwargs["headers"],
        )

    def test_timeout_fallback_does_not_start_another_retry_cycle(self):
        with patch.object(
            scraper.requests,
            "get",
            side_effect=[
                scraper.requests.exceptions.Timeout(),
                FakeResponse("", 503),
            ],
        ) as request:
            result = scraper.scrape_page_context(
                "",
                "https://example.com/collections/balloons",
            )

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "HTTP 503")
        self.assertEqual(request.call_count, 2)

    def test_scraper_does_not_retry_non_transient_http_errors(self):
        with (
            patch.object(
                scraper.requests,
                "get",
                return_value=FakeResponse("", 404),
            ) as request,
            patch("time.sleep") as sleep,
        ):
            result = scraper.scrape_page_context(
                "",
                "https://example.com/missing",
            )

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "HTTP 404")
        self.assertEqual(request.call_count, 1)
        sleep.assert_not_called()

    def test_scraper_preserves_selector_fallback_for_422(self):
        html = """
Title: Balloon Collection

This collection includes colorful balloons for birthdays, weddings, graduations, and other celebrations.
"""
        with patch.object(
            scraper.requests,
            "get",
            side_effect=[FakeResponse("", 422), FakeResponse(html)],
        ) as request:
            result = scraper.scrape_page_context(
                "",
                "https://example.com/collections/balloons",
            )

        self.assertTrue(result["success"])
        self.assertEqual(request.call_count, 2)
        self.assertNotIn(
            "X-Remove-Selector",
            request.call_args_list[1].kwargs["headers"],
        )

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
