import unittest
from unittest.mock import patch

from utils import dfs


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "tasks": [
                {
                    "result": [
                        {
                            "items": [
                                {
                                    "keyword": "easy keyword",
                                    "keyword_difficulty": 0,
                                }
                            ]
                        }
                    ]
                }
            ]
        }


class KeywordDifficultyTests(unittest.TestCase):
    @patch.object(dfs.requests, "post", return_value=FakeResponse())
    def test_dfs_parser_preserves_zero_keyword_difficulty(self, _mock_post):
        result = dfs.get_keyword_difficulty(
            "login",
            "password",
            ["easy keyword"],
        )

        self.assertEqual(result["easy keyword"]["difficulty"], 0)


if __name__ == "__main__":
    unittest.main()
