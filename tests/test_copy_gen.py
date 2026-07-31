import unittest

from utils import copy_gen


class CopyPromptTests(unittest.TestCase):
    def test_solo_and_batch_prompts_require_us_english(self):
        solo_prompt = copy_gen._build_prompt(
            keyword="running shoes",
            page_type="product",
            brand_name="Acme",
            business_type="ecommerce",
            h1="Running Shoes",
            ai_overview_sections=[],
            ai_overview_raw="",
            paa_items=[],
            num_faqs=5,
            forbidden_phrases="",
            page_context="A UK source uses colour and prioritise.",
        )
        batch_prompt = copy_gen._build_batch_prompt(
            [
                {
                    "keyword": "running shoes",
                    "page_type": "product",
                    "brand_name": "Acme",
                    "business_type": "ecommerce",
                    "h1": "Running Shoes",
                    "page_context": "A UK source uses colour and prioritise.",
                }
            ],
            5,
        )

        for prompt in (solo_prompt, batch_prompt):
            self.assertIn("U.S. ENGLISH REQUIREMENT", prompt)
            self.assertIn("Do not imitate British spelling", prompt)
            self.assertIn("Preserve official brand and product names", prompt)

    def test_provider_default_models_match_current_recommended_defaults(self):
        self.assertEqual(
            copy_gen.DEFAULT_MODELS,
            {
                "Claude": "claude-sonnet-5",
                "OpenAI": "gpt-5.5",
                "Gemini (free)": "gemini-3.5-flash",
            },
        )

    def test_sonnet_5_request_disables_thinking_for_json_tasks(self):
        options = copy_gen._anthropic_request_options("claude-sonnet-5", 2048)

        self.assertEqual(options["model"], "claude-sonnet-5")
        self.assertEqual(options["max_tokens"], 2048)
        self.assertEqual(options["extra_body"], {"thinking": {"type": "disabled"}})
        self.assertNotIn("thinking", options)

    def test_anthropic_text_extractor_skips_non_text_blocks(self):
        class Block:
            def __init__(self, type_, text=None):
                self.type = type_
                self.text = text

        self.assertEqual(
            copy_gen._extract_anthropic_text([
                Block("thinking"),
                Block("text", "Generated FAQ JSON"),
            ]),
            "Generated FAQ JSON",
        )

    def test_openai_gpt5_models_use_completion_token_parameter(self):
        self.assertEqual(
            copy_gen._openai_token_limit("gpt-5.5", 123),
            {"max_completion_tokens": 123},
        )
        self.assertEqual(
            copy_gen._openai_token_limit("gpt-5.4", 456),
            {"max_completion_tokens": 456},
        )

    def test_solo_prompt_blocks_unsupported_risky_business_claims(self):
        prompt = copy_gen._build_prompt(
            keyword="running shoes",
            page_type="product",
            brand_name="Acme",
            business_type="ecommerce",
            h1="Running Shoes",
            ai_overview_sections=[],
            ai_overview_raw="",
            paa_items=[
                {
                    "question": "Can I return running shoes after trying them?",
                    "answer": "Many stores only accept unworn products.",
                }
            ],
            num_faqs=3,
            forbidden_phrases="",
            page_context="Lightweight running shoes for daily training.",
        )

        self.assertIn("UNSUPPORTED CLAIM RULES", prompt)
        self.assertIn("Do not generate FAQ questions or answers about return", prompt)
        self.assertIn("shipping", prompt)
        self.assertIn("warranty", prompt)
        self.assertIn("availability", prompt)
        self.assertIn("Exclude these topics entirely", prompt)
        self.assertIn("Treat AI Overview and PAA as research signals, not proof", prompt)
        self.assertIn("Do not use neutral fallback wording", prompt)
        self.assertIn("Do not tell readers to check the policy page", prompt)
        self.assertIn("Prefer not to reference shipping or returns", prompt)
        self.assertIn("brand guidelines explicitly provide", prompt)
        self.assertIn("Do not repeat the exact product name more than 2 times total", prompt)
        self.assertIn("Do not use partial product-name variations", prompt)
        self.assertIn("unless the phrase is the generic item or category", prompt)
        self.assertIn("Use natural references like this product", prompt)
        self.assertIn("Use the main keyword naturally no more than 1 to 2 times total", prompt)
        self.assertIn("Do not force the exact keyword into every question or answer", prompt)

    def test_batch_prompt_blocks_unsupported_risky_business_claims(self):
        prompt = copy_gen._build_batch_prompt(
            [
                {
                    "keyword": "running shoes",
                    "page_type": "product",
                    "business_type": "ecommerce",
                    "brand_name": "Acme",
                    "h1": "Running Shoes",
                    "page_context": "Lightweight running shoes for daily training.",
                    "ai_overview_sections": [],
                    "paa_items": [
                        {
                            "question": "Are returns free?",
                            "answer": "Some stores offer free returns.",
                        }
                    ],
                }
            ],
            num_faqs=3,
        )

        self.assertIn("UNSUPPORTED CLAIM RULES", prompt)
        self.assertIn("Do not generate FAQ questions or answers about return", prompt)
        self.assertIn("shipping", prompt)
        self.assertIn("warranty", prompt)
        self.assertIn("availability", prompt)
        self.assertIn("Exclude these topics entirely", prompt)
        self.assertIn("Treat AI Overview and PAA as research signals, not proof", prompt)
        self.assertIn("Do not use neutral fallback wording", prompt)
        self.assertIn("Do not tell readers to check the policy page", prompt)
        self.assertIn("Prefer not to reference shipping or returns", prompt)
        self.assertIn("brand guidelines explicitly provide", prompt)
        self.assertIn("Do not repeat the exact product name more than 2 times total", prompt)
        self.assertIn("Do not use partial product-name variations", prompt)
        self.assertIn("unless the phrase is the generic item or category", prompt)
        self.assertIn("Use natural references like this product", prompt)
        self.assertIn("Use the main keyword naturally no more than 1 to 2 times total", prompt)
        self.assertIn("Do not force the exact keyword into every question or answer", prompt)

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
        self.assertIn("If you reference specific colors, sizes, patterns, styles, or prices", prompt)
        self.assertIn("including X and other colors", prompt)
        self.assertIn("sizes such as X and more", prompt)
        self.assertIn("Never present scraped values as a complete or exhaustive list", prompt)

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
        self.assertIn("If you reference specific colors, sizes, patterns, styles, or prices", prompt)
        self.assertIn("including X and other colors", prompt)
        self.assertIn("sizes such as X and more", prompt)
        self.assertIn("Never present scraped values as a complete or exhaustive list", prompt)

    def test_brand_guidelines_are_required_for_shipping_or_returns(self):
        prompt = copy_gen._build_prompt(
            keyword="women's shirts",
            page_type="collection",
            brand_name="Army Surplus World",
            business_type="ecommerce",
            h1="Women's Shirts",
            ai_overview_sections=[],
            ai_overview_raw="",
            paa_items=[
                {
                    "question": "What is the return policy for women's shirts?",
                    "answer": "Some stores accept unworn returns.",
                }
            ],
            num_faqs=4,
            forbidden_phrases="",
            page_context="COLLECTION CONTEXT\nProducts found:\n- Shirt | $19.99",
            brand_guidelines="Returns are accepted within 30 days for unworn items.",
        )

        self.assertIn("BRAND & COPY GUIDELINES", prompt)
        self.assertIn("Prefer not to reference shipping or returns", prompt)
        self.assertIn("Only use shipping or returns information when brand guidelines explicitly provide", prompt)
        self.assertIn("Do not use PAA, AI Overview, scraped page content, or generic ecommerce assumptions", prompt)

    def test_parse_faq_json_records_error_for_invalid_model_output(self):
        parsed = copy_gen._parse_faq_json("not json")

        self.assertEqual(parsed, [])
        self.assertIn("FAQ JSON parse failed", copy_gen.get_last_parse_error())

    def test_batch_fallback_records_solo_retry_error(self):
        def fake_provider(api_key, prompt, max_tokens=2048, model=None):
            if "PAGE 1" in prompt and "PAGE 2" in prompt:
                return '{"1": [], "2": []}'
            raise RuntimeError("provider down")

        copy_gen._PROVIDER_FN["TestProvider"] = fake_provider
        try:
            results, _prompt, debug = copy_gen.generate_faq_batch(
                provider="TestProvider",
                api_key="test",
                pages=[
                    {"keyword": "alpha", "page_type": "general", "business_type": "general"},
                    {"keyword": "beta", "page_type": "general", "business_type": "general"},
                ],
                num_faqs=2,
            )
        finally:
            copy_gen._PROVIDER_FN.pop("TestProvider", None)

        self.assertEqual(results[0], [])
        self.assertEqual(results[1], [])
        self.assertIn("provider down", copy_gen.get_last_batch_errors()[0])
        self.assertIn("BATCH FALLBACK ERROR", debug[0])


if __name__ == "__main__":
    unittest.main()
