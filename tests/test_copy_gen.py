import unittest

from utils import copy_gen


class CopyPromptTests(unittest.TestCase):
    def test_solo_ecommerce_collection_prompt_generalizes_scraped_product_details(self):
        prompt = copy_gen._build_prompt(
            keyword="running shoes",
            page_type="collection",
            brand_name="Acme",
            business_type="ecommerce",
            h1="Running Shoes",
            ai_overview_sections=[],
            ai_overview_raw="",
            paa_items=[],
            num_faqs=3,
            forbidden_phrases="",
            page_context=(
                "COLLECTION CONTEXT\n\n"
                "Products found:\n"
                "- Blue Runner Shoe | $49.99\n"
                "- Trail Grip Shoe | $69.00\n\n"
                "Filters found:\n"
                "- Size: 8, 9, 10\n"
                "- Price: $50-$100"
            ),
        )

        self.assertIn("Use ecommerce collection context as research only", prompt)
        self.assertIn("Do not mention exact prices", prompt)
        self.assertIn("Do not mention exact product counts", prompt)
        self.assertIn("Do not mention exact sizes", prompt)
        self.assertIn("Do not mention exact variant counts", prompt)
        self.assertIn("Do not quote exact product names", prompt)

    def test_batch_ecommerce_collection_prompt_generalizes_scraped_product_details(self):
        prompt = copy_gen._build_batch_prompt(
            [
                {
                    "keyword": "running shoes",
                    "page_type": "category",
                    "business_type": "ecommerce",
                    "brand_name": "Acme",
                    "h1": "Running Shoes",
                    "page_context": (
                        "COLLECTION CONTEXT\n\n"
                        "Products found:\n"
                        "- Blue Runner Shoe | $49.99\n\n"
                        "Filters found:\n"
                        "- Size: 8, 9, 10"
                    ),
                    "ai_overview_sections": [],
                    "paa_items": [],
                }
            ],
            num_faqs=3,
        )

        self.assertIn("Use ecommerce collection context as research only", prompt)
        self.assertIn("Do not mention exact prices", prompt)
        self.assertIn("Do not mention exact product counts", prompt)
        self.assertIn("Do not mention exact sizes", prompt)
        self.assertIn("Do not mention exact variant counts", prompt)
        self.assertIn("Do not quote exact product names", prompt)


if __name__ == "__main__":
    unittest.main()
