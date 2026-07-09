import unittest

from utils.keyword import select_keyword


class KeywordSelectionTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
