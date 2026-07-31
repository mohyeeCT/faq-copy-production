from pathlib import Path
import unittest


APP_SOURCE = Path(__file__).resolve().parents[1] / "app.py"


class AppRunInfoTests(unittest.TestCase):
    def test_app_displays_run_preview_and_builds_one_run_metadata_record(self):
        source = APP_SOURCE.read_text(encoding="utf-8")

        self.assertIn("estimate_faq_run(", source)
        self.assertIn('st.subheader("Run Preview")', source)
        self.assertIn("run_metadata = build_run_metadata(", source)

    def test_run_metadata_is_available_to_sheet_write_back(self):
        source = APP_SOURCE.read_text(encoding="utf-8")

        for column in ["run_id", "generated_at", "provider", "model"]:
            self.assertIn(f'"{column}":', source)


if __name__ == "__main__":
    unittest.main()
