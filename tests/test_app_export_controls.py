from pathlib import Path
import unittest


APP_SOURCE = Path(__file__).resolve().parents[1] / "app.py"
REQUIREMENTS = Path(__file__).resolve().parents[1] / "requirements.txt"


class AppExportControlsTests(unittest.TestCase):
    def test_batch_size_is_capped_at_five_pages_per_ai_call(self):
        source = APP_SOURCE.read_text(encoding="utf-8")

        self.assertIn('"Batch size (pages per AI call)"', source)
        self.assertIn("min_value=1, max_value=5, value=5", source)

    def test_excel_export_is_available(self):
        source = APP_SOURCE.read_text(encoding="utf-8")
        requirements = REQUIREMENTS.read_text(encoding="utf-8")

        self.assertIn("to_excel", source)
        self.assertIn("Download Excel", source)
        self.assertIn("openpyxl", requirements)


if __name__ == "__main__":
    unittest.main()
