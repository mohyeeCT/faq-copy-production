import unittest
from datetime import datetime, timezone

from utils.run_info import build_run_metadata, estimate_faq_run


class RunMetadataTests(unittest.TestCase):
    def test_build_run_metadata_uses_one_utc_timestamp_and_run_id(self):
        metadata = build_run_metadata(
            provider="OpenAI",
            model="gpt-5.5",
            now=datetime(2026, 7, 31, 12, 30, tzinfo=timezone.utc),
            run_id="faq-run-1",
        )

        self.assertEqual(
            metadata,
            {
                "run_id": "faq-run-1",
                "generated_at": "2026-07-31T12:30:00Z",
                "provider": "OpenAI",
                "model": "gpt-5.5",
            },
        )


class FaqRunEstimateTests(unittest.TestCase):
    def test_processing_chunks_are_reflected_in_ai_call_estimate(self):
        estimate = estimate_faq_run(
            valid_rows=12,
            gsc_enrichment_rows=7,
            batch_size=5,
            processing_chunk_size=5,
            load_async_ai_overview=True,
        )

        self.assertEqual(estimate["ai_calls"], 3)
        self.assertEqual(estimate["dfs_calls_min"], 26)
        self.assertEqual(estimate["dfs_calls_max"], 158)
        self.assertAlmostEqual(estimate["dfs_cost_min"], 0.7464)
        self.assertAlmostEqual(estimate["dfs_cost_max"], 1.3848)

    def test_single_row_processing_chunks_require_one_ai_call_per_row(self):
        estimate = estimate_faq_run(
            valid_rows=4,
            gsc_enrichment_rows=0,
            batch_size=5,
            processing_chunk_size=1,
            load_async_ai_overview=False,
        )

        self.assertEqual(estimate["ai_calls"], 4)
        self.assertAlmostEqual(estimate["dfs_cost_min"], 0.008)
        self.assertAlmostEqual(estimate["dfs_cost_max"], 0.1248)


if __name__ == "__main__":
    unittest.main()
