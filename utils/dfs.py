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


def get_serp_data(login: str, password: str, keyword: str, location_code: int = 2840) -> dict:
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
    }

    if not keyword:
        return empty

    payload = [{
        "keyword": keyword,
        "location_code": location_code,
        "language_code": "en",
        "depth": 10,
        "people_also_ask_click_depth": 2,
    }]

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

        for task in data.get("tasks", []):
            for result_block in (task.get("result") or []):
                for item in (result_block.get("items") or []):
                    item_type = item.get("type", "")

                    # ── AI Overview ──────────────────────────────────────────
                    if item_type in ("ai_overview", "asynchronous_ai_overview"):
                        for block in (item.get("items") or []):
                            block_type = block.get("type", "")

                            # Section with a title
                            if block_type == "ai_overview_element" or block.get("title"):
                                title = block.get("title", "").strip()
                                # Content may be nested in sub-items or in text field
                                content_parts = []
                                for sub in (block.get("items") or []):
                                    txt = sub.get("text", "") or sub.get("content", "")
                                    if txt:
                                        content_parts.append(txt.strip())
                                if not content_parts:
                                    content_parts = [block.get("text", "").strip()]

                                content = " ".join(filter(None, content_parts))
                                if title or content:
                                    ai_sections.append({
                                        "title": title,
                                        "content": content
                                    })
                                    if title:
                                        ai_raw_parts.append(f"{title}: {content}")
                                    else:
                                        ai_raw_parts.append(content)

                            # Plain text block without a title
                            elif block.get("text"):
                                txt = block["text"].strip()
                                if txt:
                                    ai_sections.append({"title": "", "content": txt})
                                    ai_raw_parts.append(txt)

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
                            # Extract best available answer snippet
                            answer = ""
                            for result_item in (paa_el.get("items") or []):
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

        # asynchronous_ai_overview means Google has one but DFS couldn't
        # capture the content because it loads via JS after page load
        async_ao_detected = "asynchronous_ai_overview" in all_item_types

        return {
            "ai_overview_present": len(ai_sections) > 0,
            "ai_overview_async_only": async_ao_detected and len(ai_sections) == 0,
            "ai_overview_sections": ai_sections,
            "ai_overview_raw": "\n".join(ai_raw_parts),
            "paa_questions": paa_questions,
            "paa_items": paa_items,
            "serp_item_types": all_item_types,
            "paa_raw_debug": str(paa_raw_items[:1])[:500] if paa_raw_items else "",
        }

    except Exception as e:
        result = empty.copy()
        result["error"] = str(e)
        return result
