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
    """Positions 1-20 score 1.0. Beyond 20 drops off.
    Formula: 1 / (1 + max(0, position - 20) * 0.1)
    """
    return 1 / (1 + max(0, position - 20) * 0.1)


def select_keyword(
    gsc_queries: list,
    dfs_data: dict,
    branded_terms: list,
    min_volume: int = 10,
    h1: str = "",
    restricted_industry: bool = False,
) -> dict:
    """Score and rank GSC queries. Return selected keyword and runner-up.

    Changes from original:
    - CTR capped at 0.15 to prevent outlier CTR from dominating scores
    - restricted_industry mode: ignores volume/difficulty, scores on GSC signals only.
      Used for industries where DFS suppresses volume data (CBD, guns, dispensaries, adult).
    - Zero-volume keywords: scored with 0.1 proxy penalty in standard mode (not dropped).
      In restricted_industry mode they compete on equal footing.
    - position_cutoff: only excludes exact position 1.0
    - branded filtering: substring match
    """

    def is_branded(query: str) -> bool:
        q_lower = query.lower()
        return any(b.lower() in q_lower for b in branded_terms if b)

    candidates = []

    for q in gsc_queries:
        query = q["query"]
        position = q.get("position", 99.0)
        impressions = q.get("impressions", 0)
        clicks = q.get("clicks", 0)
        ctr = min(q.get("ctr", 0.0), 0.15)  # cap CTR at 15%

        if is_branded(query):
            continue
        if position == 1.0:
            continue

        dfs = dfs_data.get(query.lower(), {})
        volume = dfs.get("volume", 0) or 0
        difficulty = dfs.get("difficulty", 50) or 50

        pos_score = _position_score(position)
        rel_score = _relevance_score(query, h1)
        ctr_boost = 1 + ctr

        if volume == 0:
            if impressions > 0:
                if restricted_industry:
                    # Restricted: score on engagement alone, no penalty
                    clicks_boost = max(math.log1p(clicks), 1.0)
                    sc = math.log1p(impressions) * clicks_boost * ctr_boost * pos_score * rel_score
                else:
                    # Standard: apply 0.1 penalty so these rank below volume-bearing keywords
                    sc = math.log1p(impressions) * ctr_boost * 0.1
                candidates.append({
                    "keyword": query,
                    "score": round(sc, 4),
                    "volume": 0,
                    "difficulty": difficulty,
                })
            continue

        if not restricted_industry and volume < min_volume:
            continue

        if restricted_industry:
            # Ignore volume/difficulty entirely - level playing field
            clicks_boost = max(math.log1p(clicks), 1.0)
            sc = math.log1p(impressions) * clicks_boost * ctr_boost * pos_score * rel_score
        else:
            sc = (volume / difficulty) * math.log1p(impressions) * ctr_boost * pos_score * rel_score

        candidates.append({
            "keyword": query,
            "score": round(sc, 4),
            "volume": volume,
            "difficulty": difficulty,
        })

    if not candidates:
        return {
            "selected_keyword": None,
            "selected_keyword_data": None,
            "runner_up": None,
            "fallback_triggered": True,
        }

    candidates.sort(key=lambda x: x["score"], reverse=True)

    return {
        "selected_keyword": candidates[0]["keyword"],
        "selected_keyword_data": candidates[0],
        "runner_up": candidates[1] if len(candidates) > 1 else None,
        "fallback_triggered": False,
    }
