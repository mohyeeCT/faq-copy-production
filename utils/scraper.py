import re
import requests

JINA_BASE = "https://r.jina.ai"

# Elements to strip server-side via Jina's X-Remove-Selector.
# More reliable than X-Target-Selector because we remove known noise
# rather than trying to guess content class names per platform.
_REMOVE_SELECTOR = ", ".join([
    "nav", "header", "footer", "aside",
    "#cart", ".cart", "[class*='cart']",
    "#header", "#footer", "#nav", "#sidebar",
    "[class*='sidebar']", "[class*='navigation']",
    "[class*='breadcrumb']", "[class*='cookie']",
    "[class*='popup']", "[class*='modal']",
    "[class*='newsletter']", "[class*='subscribe']",
    "[class*='related']", "[class*='recommended']",
    "[class*='upsell']", "[class*='cross-sell']",
    "form", "script", "style", "noscript", "iframe",
])

# Lines that are almost certainly noise regardless of platform
_NOISE_LINE_PATTERNS = re.compile(
    r"^\s*("
    r"\$[\d,.]+|"                          # prices
    r"Add to cart|Sold out|Sale price|"
    r"Regular price|Unit price|"
    r"Quantity must be|Adding product|"
    r"Please allow \d|"
    r"Pickup available|Usually ready|"
    r"Check availability|Service Center|"
    r"Skip to content|Log in|Sign in|"
    r"Search$|Menu$|Close$|"
    r"\+?1?[\s\-.]?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}"  # phone numbers
    r")\s*$",
    re.IGNORECASE
)


def _score_paragraph(para: str) -> float:
    """Score a paragraph by content quality. Higher = more substantive.

    Penalises: short lines, link-heavy lines, price/button text.
    Rewards: sentence-like text with multiple words.
    """
    words = para.split()
    if len(words) < 8:
        return 0.0

    # Penalise link density
    link_count = len(re.findall(r"\[.+?\]\(https?://", para))
    if link_count > 2:
        return 0.0

    # Penalise lines that are mostly numbers or special chars
    alpha_ratio = sum(c.isalpha() for c in para) / max(len(para), 1)
    if alpha_ratio < 0.5:
        return 0.0

    # Score = word count * alpha ratio
    return len(words) * alpha_ratio


def scrape_page_context(api_key: str, url: str, max_chars: int = 4000) -> dict:
    """Scrape a page via Jina Reader and return cleaned topic context.

    Strategy:
    1. Use X-Remove-Selector to strip nav/cart/footer server-side
    2. Post-process: score each paragraph by content density
    3. Keep highest-scoring paragraphs up to max_chars
    4. Works on any platform — no CSS class guessing required

    Returns:
        {"content": str, "title": str, "success": bool, "error": str}
    """
    if not url:
        return {"content": "", "title": "", "success": False, "error": "No URL provided"}

    headers = {
        "Accept": "text/plain",
        "X-Return-Format": "markdown",
        "X-With-Links-Summary": "false",
        "X-With-Images-Summary": "false",
        "X-Remove-Selector": _REMOVE_SELECTOR,
        "X-Timeout": "30",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.get(f"{JINA_BASE}/{url}", headers=headers, timeout=35)

        # If remove selector causes issues, retry clean
        if resp.status_code in (422, 400):
            headers.pop("X-Remove-Selector", None)
            resp = requests.get(f"{JINA_BASE}/{url}", headers=headers, timeout=35)

        resp.raise_for_status()
        text = resp.text.strip()

        if not text:
            return {"content": "", "title": "", "success": False,
                    "error": "Jina returned empty content"}

        # Extract title from Jina metadata block
        title = ""
        title_match = re.search(r"^Title:\s*(.+)$", text, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()

        # Drop image lines, pure link-list lines, and heading-wrapped links
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"^\s*\*\s+\[.+?\]\(https?://.+?\)\s*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"^#{1,4}\s+\[.+?\]\(https?://.+?\)\s*$", "", text, flags=re.MULTILINE)

        # Drop known noise lines
        lines = text.splitlines()
        lines = [l for l in lines if not _NOISE_LINE_PATTERNS.match(l)]
        text = "\n".join(lines)

        # Collapse whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        if not text:
            return {"content": "", "title": title, "success": False,
                    "error": "No content found after stripping boilerplate"}

        # Score paragraphs and keep the best ones up to max_chars
        paragraphs = re.split(r"\n{2,}", text)
        scored = [(p, _score_paragraph(p)) for p in paragraphs]

        # Always keep headings (## lines) as they provide structure context
        # Sort non-heading paragraphs by score, then interleave with headings
        # to preserve reading order in the final output
        result_paras = []
        chars_used = 0
        for para, score in scored:
            if chars_used >= max_chars:
                break
            is_heading = para.strip().startswith("#")
            if score > 0 or is_heading:
                result_paras.append(para)
                chars_used += len(para)

        content = "\n\n".join(result_paras).strip()

        # Final trim to max_chars at sentence boundary
        if len(content) > max_chars:
            truncated = content[:max_chars]
            last_period = truncated.rfind(".")
            if last_period > max_chars * 0.5:
                content = truncated[: last_period + 1].strip()
            else:
                content = truncated.strip()

        if not content:
            return {"content": "", "title": title, "success": False,
                    "error": "No substantive content found after scoring"}

        return {"content": content, "title": title, "success": True, "error": ""}

    except requests.exceptions.Timeout:
        return {"content": "", "title": "", "success": False, "error": "Request timed out"}
    except requests.exceptions.HTTPError as e:
        return {"content": "", "title": "", "success": False, "error": f"HTTP {e.response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"content": "", "title": "", "success": False, "error": str(e)}
    except Exception as e:
        return {"content": "", "title": "", "success": False, "error": str(e)}
