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


def get_people_also_ask(login: str, password: str, keyword: str, location_code: int = 2840) -> list:
    """Fetch PAA questions for a keyword via DataForSEO SERP organic live advanced.
    Returns a list of question strings (up to 8). Returns [] on failure.
    PAA items appear as type='people_also_ask' blocks inside the SERP results.
    """
    if not keyword:
        return []

    payload = [{
        "keyword": keyword,
        "location_code": location_code,
        "language_code": "en",
        "depth": 10
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

        questions = []
        for task in data.get("tasks", []):
            for result_block in (task.get("result") or []):
                for item in (result_block.get("items") or []):
                    if item.get("type") == "people_also_ask":
                        for paa_element in (item.get("items") or []):
                            q = paa_element.get("title", "").strip()
                            if q and q not in questions:
                                questions.append(q)
                    if len(questions) >= 8:
                        break
                if len(questions) >= 8:
                    break

        return questions

    except Exception:
        return []
