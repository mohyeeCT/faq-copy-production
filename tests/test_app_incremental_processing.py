from pathlib import Path
import unittest


APP_SOURCE = Path(__file__).resolve().parents[1] / "app.py"


class AppIncrementalProcessingTests(unittest.TestCase):
    def test_app_exposes_incremental_processing_controls(self):
        source = APP_SOURCE.read_text(encoding="utf-8")

        self.assertIn("Processing chunk size", source)
        self.assertIn("Auto-write completed chunks to Google Sheet", source)

    def test_app_stores_and_displays_partial_results_during_run(self):
        source = APP_SOURCE.read_text(encoding="utf-8")

        self.assertIn('st.session_state["partial_results"]', source)
        self.assertIn("partial_results_placeholder", source)

    def test_app_can_write_completed_chunks_with_shared_sheet_mapping(self):
        source = APP_SOURCE.read_text(encoding="utf-8")

        self.assertIn("RESULT_COL_MAP", source)
        self.assertIn("write_results_to_sheet(ws, pd.DataFrame(results), RESULT_COL_MAP)", source)


if __name__ == "__main__":
    unittest.main()
