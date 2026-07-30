import unittest

from utils.keyword import resolve_h1_keyword_fallback, select_keyword


class KeywordSelectionTests(unittest.TestCase):
    def test_h1_is_used_when_gsc_and_manual_keyword_are_unavailable(self):
        keyword, source = resolve_h1_keyword_fallback("  Men's Waterproof Hiking Boots  ")

        self.assertEqual(keyword, "Men's Waterproof Hiking Boots")
        self.assertEqual(source, "h1 fallback")

    def test_blank_h1_values_preserve_skip_behavior(self):
        for h1 in ("", None, "none", "NaN"):
            with self.subTest(h1=h1):
                keyword, source = resolve_h1_keyword_fallback(h1)

                self.assertIsNone(keyword)
                self.assertEqual(
                    source,
                    "skipped: GSC disabled and no keyword or H1 in sheet",
                )

    def test_standard_zero_volume_scoring_uses_position_and_h1_relevance(self):
        queries = [
            {"query": "random shoes", "impressions": 10000, "clicks": 200, "ctr": 0.15, "position": 80.0},
            {"query": "running shoes", "impressions": 1000, "clicks": 30, "ctr": 0.05, "position": 5.0},
        ]

        result = select_keyword(
            gsc_queries=queries,
            dfs_data={},
            branded_terms=[],
            h1="Running Shoes",
            restricted_industry=False,
        )

        self.assertEqual(result["selected_keyword"], "running shoes")

    def test_zero_difficulty_is_clamped_to_one_for_scoring(self):
        result = select_keyword(
            gsc_queries=[
                {
                    "query": "easy keyword",
                    "impressions": 100,
                    "clicks": 5,
                    "ctr": 0.05,
                    "position": 5.0,
                }
            ],
            dfs_data={
                "easy keyword": {
                    "volume": 100,
                    "difficulty": 0,
                }
            },
            branded_terms=[],
        )

        self.assertEqual(result["selected_keyword_data"]["difficulty"], 1)


if __name__ == "__main__":
    unittest.main()
