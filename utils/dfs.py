import requests
import base64

DFS_BASE = "https://api.dataforseo.com/v3"


def _auth_header(login: str, password: str) -> dict:
    token = base64.b64encode(f"{login}:{password}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }


def get_keyword_overview(login: str, password: str, keywords: list, location_code: int = 2840) -> dict:
    """Returns dict keyed by lowercase keyword: {volume, cpc, competition}."""
    if not keywords:
        return {}
    payload = [{"keywords": keywords, "location_code": location_code, "language_code": "en"}]
    try:
        r = requests.post(
            f"{DFS_BASE}/keywords_data/google_ads/search_volume/live",
            headers=_auth_header(login, password),
            json=payload,
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
        result = {}
        for task in data.get("tasks", []):
            for item in (task.get("result") or []):
                kw = item.get("keyword", "").lower()
                result[kw] = {
                    "volume": item.get("search_volume", 0) or 0,
                    "cpc": item.get("cpc", 0),
                    "competition": item.get("competition", 0)
                }
        return result
    except Exception:
        return {}


def get_keyword_difficulty(login: str, password: str, keywords: list, location_code: int = 2840) -> dict:
    """Returns dict keyed by lowercase keyword: {difficulty}."""
    if not keywords:
        return {}
    payload = [{"keywords": keywords, "location_code": location_code, "language_code": "en"}]
    try:
        r = requests.post(
            f"{DFS_BASE}/dataforseo_labs/google/bulk_keyword_difficulty/live",
            headers=_auth_header(login, password),
            json=payload,
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
        result = {}
        for task in data.get("tasks", []):
            for item in (task.get("result") or []):
                for kw_item in (item.get("items") or []):
                    kw = kw_item.get("keyword", "").lower()
                    result[kw] = {
                        "difficulty": kw_item.get("keyword_difficulty", 50) or 50
                    }
        return result
    except Exception:
        return {}



def _extract_ai_overview_text(item: dict) -> str:
    """Extract AI Overview text from a DFS SERP item.

    Mirrors the SF script approach: no assumptions about block.type,
    just pull text from wherever it exists in the response.

    Priority order:
    1. item.items[].text  (structured blocks)
    2. item.text          (flat text field)
    3. item.markdown      (markdown fallback for async overviews)
    """
    if not item:
        return ""

    # 1. Try structured items array — map each block's text field
    blocks = item.get("items") or []
    if blocks:
        parts = []
        for block in blocks:
            txt = ""
            if isinstance(block, dict):
                txt = (
                    block.get("text", "")
                    or block.get("content", "")
                    or ""
                ).strip()
            if txt:
                parts.append(txt)
        combined = "\n\n".join(parts)
        if combined:
            return combined

    # 2. Try flat text field on the item itself
    flat = (item.get("text") or "").strip()
    if flat:
        return flat

    # 3. Try markdown field — present on some async AI Overview responses
    markdown = (item.get("markdown") or "").strip()
    if markdown:
        # Strip markdown syntax to plain text
        import re
        markdown = re.sub(r"!\[([^\]]*)\]\((https?://[^\)]+)\)", r"\1", markdown)
        markdown = re.sub(r"\[([^\]]+)\]\((https?://[^\)]+)\)", r"\1", markdown)
        markdown = re.sub(r"https?://\S+", "", markdown)
        markdown = re.sub(r"\*+", "", markdown)
        markdown = re.sub(r"#+\s*", "", markdown)
        markdown = re.sub(r"\s+", " ", markdown).strip()
        if markdown:
            return markdown

    return ""



def get_serp_data(login: str, password: str, keyword: str, location_code: int = 2840, load_async_ai_overview: bool = True) -> dict:
    """Single SERP call that returns both AI Overview and PAA data.

    Returns:
    {
        "ai_overview_present": bool,
        "ai_overview_sections": [{"title": str, "content": str}, ...],
        "ai_overview_raw": str,          # full concatenated AI overview text
        "paa_questions": [str, ...],     # PAA question strings
        "paa_items": [{"question": str, "answer": str, "url": str}, ...]
    }
    """
    empty = {
        "ai_overview_present": False,
        "ai_overview_async_only": False,
        "ai_overview_sections": [],
        "ai_overview_raw": "",
        "paa_questions": [],
        "paa_items": [],
        "serp_item_types": [],
        "paa_raw_debug": "",
        "ao_raw_debug": "",
        "ao_raw_found": False,
        "ao_attempts": 0,
    }

    if not keyword:
        return empty

    payload = [{
        "keyword": keyword,
        "location_code": location_code,
        "language_code": "en",
        "depth": 10,
        "people_also_ask_click_depth": 4,
        "load_async_ai_overview": load_async_ai_overview,
    }]

    max_attempts = 3
    last_error = None

    for attempt in range(1, max_attempts + 1):
      try:
        r = requests.post(
            f"{DFS_BASE}/serp/google/organic/live/advanced",
            headers=_auth_header(login, password),
            json=payload,
            timeout=45
        )
        r.raise_for_status()
        data = r.json()

        ai_sections = []
        ai_raw_parts = []
        paa_questions = []
        paa_items = []
        paa_raw_items = []
        ao_raw_items = []

        for task in data.get("tasks", []):
            for result_block in (task.get("result") or []):
                for item in (result_block.get("items") or []):
                    item_type = item.get("type", "")

                    # ── AI Overview ──────────────────────────────────────────
                    if item_type in ("ai_overview", "asynchronous_ai_overview"):
                        ao_raw_items.append(item)
                        ao_text = _extract_ai_overview_text(item)
                        if ao_text:
                            ai_sections.append({"title": "", "content": ao_text})
                            ai_raw_parts.append(ao_text)

                    # ── PAA ──────────────────────────────────────────────────
                    if item_type == "people_also_ask":
                        paa_raw_items.append(item)
                        for paa_el in (item.get("items") or []):
                            # DFS uses "title" for the question text,
                            # but fall back to other fields defensively
                            q = (
                                paa_el.get("title", "")
                                or paa_el.get("question", "")
                                or paa_el.get("name", "")
                                or paa_el.get("text", "")
                            ).strip()
                            if not q or q in paa_questions:
                                continue
                            paa_questions.append(q)
                            # Extract answer from expanded_element (DFS structure)
                            # Falls back to items[] for older response formats
                            answer = ""
                            answer_source = (
                                paa_el.get("expanded_element") or
                                paa_el.get("items") or
                                []
                            )
                            for result_item in answer_source:
                                answer = (
                                    result_item.get("description", "")
                                    or result_item.get("text", "")
                                    or result_item.get("snippet", "")
                                    or ""
                                ).strip()
                                if answer:
                                    break
                            paa_items.append({
                                "question": q,
                                "answer": answer,
                                "url": paa_el.get("url", "")
                            })

        # Collect all item types for debugging
        all_item_types = []
        for task in data.get("tasks", []):
            for result_block in (task.get("result") or []):
                for item in (result_block.get("items") or []):
                    t = item.get("type", "unknown")
                    if t not in all_item_types:
                        all_item_types.append(t)

        async_ao_detected = "asynchronous_ai_overview" in all_item_types
        ao_found = len(ai_sections) > 0

        result = {
            "ai_overview_present": ao_found,
            "ai_overview_async_only": async_ao_detected and not ao_found,
            "ai_overview_sections": ai_sections,
            "ai_overview_raw": "\n".join(ai_raw_parts),
            "paa_questions": paa_questions,
            "paa_items": paa_items,
            "serp_item_types": all_item_types,
            "paa_raw_debug": str(paa_raw_items[:1])[:500] if paa_raw_items else "",
            "ao_raw_debug": str(ao_raw_items[:1])[:800] if ao_raw_items else "",
            "ao_raw_found": len(ao_raw_items) > 0,
            "ao_attempts": attempt,
        }

        # AI Overview found — no need to retry
        if ao_found:
            return result

        # No AI Overview content yet — retry if attempts remain
        if attempt < max_attempts:
            import time as _time
            _time.sleep(2)
            continue

        # Exhausted all attempts — return best result so far
        return result

      except Exception as e:
        last_error = str(e)
        if attempt < max_attempts:
            import time as _time
            _time.sleep(2)
            continue
        result = empty.copy()
        result["error"] = last_error
        result["ao_attempts"] = attempt
        return result
