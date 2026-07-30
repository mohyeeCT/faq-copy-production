from pathlib import Path
import unittest


APP_SOURCE = Path(__file__).resolve().parents[1] / "app.py"


class AppPageInputTests(unittest.TestCase):
    def test_app_normalizes_page_type_before_processing(self):
        source = APP_SOURCE.read_text(encoding="utf-8")

        self.assertIn("from utils.page_types import normalize_page_type", source)
        self.assertIn("page_type = normalize_page_type(page_type)", source)

    def test_app_uses_h1_fallback_when_gsc_is_disabled(self):
        source = APP_SOURCE.read_text(encoding="utf-8")

        self.assertIn("resolve_h1_keyword_fallback", source)
        self.assertIn(
            "selected_keyword, keyword_source = resolve_h1_keyword_fallback(h1_value)",
            source,
        )
        self.assertIn("then the H1 column as a fallback", source)


if __name__ == "__main__":
    unittest.main()
