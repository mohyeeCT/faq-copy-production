import math
import re


def _stem(word: str) -> str:
    """Minimal suffix stripping for relevance overlap scoring."""
    word = word.lower()
    for suffix in ("ing", "tion", "ed", "er", "ly", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def _relevance_score(query: str, h1: str) -> float:
    """Word overlap between query and H1 using basic stemming. Range 0.5 to 1.5."""
    if not h1:
        return 1.0
    q_stems = {_stem(w) for w in re.findall(r"[a-z]+", query.lower())}
    h_stems = {_stem(w) for w in re.findall(r"[a-z]+", h1.lower())}
    overlap = len(q_stems & h_stems)
    ratio = overlap / max(len(q_stems), 1)
    return round(min(1.5, 0.5 + ratio), 3)


def _position_score(position: float) -> float:
    """Positions 1-20 score 1.0. Beyond 20 drops off."""
    if position <= 20:
        return 1.0
    return max(0.1, 1.0 - (position - 20) * 0.05)


def score_query(query_data: dict, dfs_data: dict, h1: str = "") -> float:
    """
    score = (volume / difficulty) * log1p(impressions) * (1 + CTR) * position_score * relevance_score
    Returns 0.0 if volume is zero.
    """
    query = query_data["query"].lower()
    impressions = query_data.get("impressions", 0)
    ctr = query_data.get("ctr", 0.0)
    position = query_data.get("position", 99.0)

    dfs = dfs_data.get(query, {})
    volume = dfs.get("volume", 0) or 0
    difficulty = dfs.get("difficulty", 50) or 50

    if volume == 0:
        return 0.0

    pos_score = _position_score(position)
    rel_score = _relevance_score(query, h1)

    score = (volume / difficulty) * math.log1p(impressions) * (1 + ctr) * pos_score * rel_score
    return round(score, 4)


def select_keyword(
    gsc_queries: list,
    dfs_data: dict,
    branded_terms: list,
    min_volume: int = 10,
    h1: str = ""
) -> dict:
    """Score and rank GSC queries. Return selected keyword and runner-up.

    position_cutoff: only exclude exact position 1.0 (not position 1.x or 2+).
    branded filtering: substring match (not exact).
    """

    def is_branded(query: str) -> bool:
        q_lower = query.lower()
        return any(b.lower() in q_lower for b in branded_terms if b)

    candidates = []
    for q in gsc_queries:
        query = q["query"]
        position = q.get("position", 99.0)

        if is_branded(query):
            continue
        if position == 1.0:
            continue

        dfs = dfs_data.get(query.lower(), {})
        volume = dfs.get("volume", 0) or 0
        if volume < min_volume:
            continue

        sc = score_query(q, dfs_data, h1)
        candidates.append({
            "keyword": query,
            "score": sc,
            "volume": volume,
            "difficulty": dfs.get("difficulty", 50)
        })

    if not candidates:
        return {
            "selected_keyword": None,
            "selected_keyword_data": None,
            "runner_up": None,
            "fallback_triggered": True
        }

    candidates.sort(key=lambda x: x["score"], reverse=True)

    return {
        "selected_keyword": candidates[0]["keyword"],
        "selected_keyword_data": candidates[0],
        "runner_up": candidates[1] if len(candidates) > 1 else None,
        "fallback_triggered": False
    }
