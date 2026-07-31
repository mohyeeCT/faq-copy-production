from datetime import datetime, timezone
from math import ceil
from uuid import uuid4


# DataForSEO public list pricing checked 2026-07-31.
GOOGLE_ADS_LIVE_TASK_COST = 0.09
LABS_LIVE_TASK_COST = 0.012
LABS_LIVE_ITEM_COST = 0.00012
GSC_KEYWORDS_PER_ROW = 10
SERP_LIVE_BASE_COST = 0.002
SERP_ASYNC_AIO_COST = 0.002
SERP_PAA_CLICK_COST = 0.00015
SERP_PAA_CLICK_DEPTH = 4
SERP_ATTEMPTS_PER_QUERY = 3
SERP_QUERY_VARIANTS = 4


def build_run_metadata(
    provider: str,
    model: str,
    now: datetime | None = None,
    run_id: str | None = None,
) -> dict:
    generated_at = now or datetime.now(timezone.utc)
    generated_at = generated_at.astimezone(timezone.utc)
    return {
        "run_id": run_id or str(uuid4()),
        "generated_at": generated_at.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "provider": provider,
        "model": model or "",
    }


def _estimate_ai_calls(rows: int, batch_size: int, processing_chunk_size: int) -> int:
    rows = max(int(rows), 0)
    batch_size = max(int(batch_size), 1)
    processing_chunk_size = max(int(processing_chunk_size), 1)
    full_chunks, remainder = divmod(rows, processing_chunk_size)
    calls = full_chunks * ceil(processing_chunk_size / batch_size)
    if remainder:
        calls += ceil(remainder / batch_size)
    return calls


def estimate_faq_run(
    valid_rows: int,
    gsc_enrichment_rows: int,
    batch_size: int,
    processing_chunk_size: int,
    load_async_ai_overview: bool,
) -> dict:
    rows = max(int(valid_rows), 0)
    enrichment_rows = min(max(int(gsc_enrichment_rows), 0), rows)

    keyword_cost_per_row = (
        GOOGLE_ADS_LIVE_TASK_COST
        + LABS_LIVE_TASK_COST
        + (GSC_KEYWORDS_PER_ROW * LABS_LIVE_ITEM_COST)
    )
    keyword_cost = enrichment_rows * keyword_cost_per_row
    keyword_calls = enrichment_rows * 2

    min_serp_calls = rows
    max_serp_calls = rows * SERP_ATTEMPTS_PER_QUERY * SERP_QUERY_VARIANTS
    max_serp_cost = (
        SERP_LIVE_BASE_COST
        + (SERP_ASYNC_AIO_COST if load_async_ai_overview else 0)
        + (SERP_PAA_CLICK_COST * SERP_PAA_CLICK_DEPTH)
    )

    return {
        "rows": rows,
        "ai_calls": _estimate_ai_calls(rows, batch_size, processing_chunk_size),
        "dfs_calls_min": keyword_calls + min_serp_calls,
        "dfs_calls_max": keyword_calls + max_serp_calls,
        "dfs_cost_min": keyword_cost + (min_serp_calls * SERP_LIVE_BASE_COST),
        "dfs_cost_max": keyword_cost + (max_serp_calls * max_serp_cost),
    }
