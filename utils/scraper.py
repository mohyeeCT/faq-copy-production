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

_COLLECTION_REMOVE_SELECTOR = ", ".join([
    "nav", "header", "footer",
    "#cart", ".cart", "[class*='cart']",
    "#header", "#footer", "#nav",
    "[class*='navigation']", "[class*='breadcrumb']", "[class*='cookie']",
    "[class*='popup']", "[class*='modal']",
    "[class*='newsletter']", "[class*='subscribe']",
    "[class*='related']", "[class*='recommended']",
    "[class*='upsell']", "[class*='cross-sell']",
    "script", "style", "noscript", "iframe",
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
    r"This page does not seem to contain|"  # Jina metadata placeholders
    r"\+?1?[\s\-.]?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}"  # phone numbers
    r")\s*$",
    re.IGNORECASE
)

_COLLECTION_NOISE_LINE_PATTERNS = re.compile(
    r"^\s*("
    r"Add to cart|Sold out|Sale price|Regular price|Unit price|"
    r"Quantity must be|Adding product|"
    r"Please allow \d|"
    r"Pickup available|Usually ready|"
    r"Check availability|Service Center|"
    r"Skip to content|Log in|Sign in|"
    r"Search$|Menu$|Close$|Footer$|"
    r"\+?1?[\s\-.]?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}"
    r")\s*$",
    re.IGNORECASE
)

_PRICE_RE = re.compile(r"(?:[$£€]\s?\d[\d,.]*(?:\.\d{2})?|\d[\d,.]*(?:\.\d{2})?\s?(?:USD|GBP|EUR))")
_PRODUCT_LINK_RE = re.compile(r"^\s*#{0,4}\s*(?:[-*]\s*)?\[(?P<name>[^\]]{3,})\]\(https?://[^\)]+\)\s*$")
_FILTER_LABELS = {
    "brand", "brands", "size", "sizes", "color", "colour", "colors", "colours",
    "price", "material", "materials", "style", "styles", "type", "types",
    "category", "categories", "availability", "product type", "fit", "capacity",
    "flavor", "flavour", "weight", "finish", "features",
}


def is_ecommerce_collection_page(business_type: str, page_type: str) -> bool:
    """Return True when the row should use collection/product-grid scraping."""
    if (business_type or "").strip().lower() != "ecommerce":
        return False
    page_type_norm = (page_type or "").strip().lower()
    return "category" in page_type_norm or "collection" in page_type_norm


def _score_paragraph(para: str) -> float:
    """Score a paragraph by content quality. Higher = more substantive.

    Penalises: short lines, link-heavy lines, price/button text.
    Rewards: sentence-like text with multiple words.

    Threshold is 5 words (not 8) — noise items like "Add to cart",
    "Sold out", "Check availability" are already caught by
    _NOISE_LINE_PATTERNS before scoring, so the word floor only
    needs to block truly empty or single-token remnants.
    """
    words = para.split()
    if len(words) < 5:
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


def _extract_title(text: str) -> str:
    title_match = re.search(r"^Title:\s*(.+)$", text, re.MULTILINE)
    return title_match.group(1).strip() if title_match else ""


def _normalise_lines(text: str, noise_pattern: re.Pattern) -> list:
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or noise_pattern.match(line):
            continue
        lines.append(line)
    return lines


def _extract_collection_products(lines: list, limit: int = 30) -> list:
    products = []
    for idx, line in enumerate(lines):
        match = _PRODUCT_LINK_RE.match(line)
        if not match:
            continue
        name = re.sub(r"\s+", " ", match.group("name")).strip()
        price = ""
        for follow in lines[idx + 1: idx + 5]:
            price_match = _PRICE_RE.search(follow)
            if price_match:
                price = price_match.group(0).strip()
                break
            if _PRODUCT_LINK_RE.match(follow):
                break
        if name and not any(p["name"].lower() == name.lower() for p in products):
            products.append({"name": name, "price": price})
        if len(products) >= limit:
            break
    return products


def _extract_collection_filters(lines: list) -> dict:
    filters = {}
    current = None
    seen_filter_anchor = False

    for line in lines:
        clean = re.sub(r"^#+\s*", "", line).strip()
        clean = re.sub(r"^\*\s*", "", clean).strip()
        clean_l = clean.lower().rstrip(":")

        if clean_l == "filters":
            seen_filter_anchor = True
            current = None
            continue
        if _PRODUCT_LINK_RE.match(line):
            current = None
            continue
        if clean_l in _FILTER_LABELS:
            seen_filter_anchor = True
            current = clean.rstrip(":")
            filters.setdefault(current, [])
            continue
        if not seen_filter_anchor or not current:
            continue
        if _PRICE_RE.search(clean) and current.lower() != "price":
            continue
        if len(clean) > 40:
            current = None
            continue
        if clean and clean not in filters[current]:
            filters[current].append(clean)

    return {k: v[:12] for k, v in filters.items() if v}


def _build_collection_context(text: str, max_chars: int) -> tuple:
    title = _extract_title(text)
    lines = _normalise_lines(text, _COLLECTION_NOISE_LINE_PATTERNS)
    products = _extract_collection_products(lines)
    filters = _extract_collection_filters(lines)

    excerpt_text = "\n".join(lines)
    excerpt_text = re.sub(r"^\s*\*\s+\[.+?\]\(https?://.+?\)\s*$", "", excerpt_text, flags=re.MULTILINE)
    excerpt_text = re.sub(r"^#{1,4}\s+\[.+?\]\(https?://.+?\)\s*$", "", excerpt_text, flags=re.MULTILINE)
    excerpt_text = re.sub(r"\n{3,}", "\n\n", excerpt_text).strip()

    paragraphs = re.split(r"\n{2,}", excerpt_text)
    excerpt_parts = []
    chars_used = 0
    for para in paragraphs:
        if chars_used >= max_chars // 2:
            break
        if _score_paragraph(para) > 0 or para.strip().startswith("#"):
            excerpt_parts.append(para)
            chars_used += len(para)

    sections = ["COLLECTION CONTEXT"]
    if products:
        sections.append(
            "Products found:\n" + "\n".join(
                f"- {p['name']} | {p['price']}" if p["price"] else f"- {p['name']}"
                for p in products
            )
        )
    if filters:
        sections.append(
            "Filters found:\n" + "\n".join(
                f"- {name}: {', '.join(values)}"
                for name, values in filters.items()
            )
        )
    if excerpt_parts:
        sections.append("Page excerpt:\n" + "\n\n".join(excerpt_parts))

    content = "\n\n".join(sections).strip()
    if len(content) > max_chars:
        content = content[:max_chars].strip()
    return content, title


def _process_default_text(text: str, max_chars: int, noise_pattern: re.Pattern) -> tuple:
    """Process raw Jina markdown into clean page context for default (non-collection) mode.

    Returns (content, title).  content is "" if nothing substantive survived.
    """
    title = _extract_title(text)

    # Drop image syntax, pure link-only list lines, heading-only link lines
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"^\s*\*\s+\[.+?\]\(https?://.+?\)\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^#{1,4}\s+\[.+?\]\(https?://.+?\)\s*$", "", text, flags=re.MULTILINE)

    # Drop noise lines
    lines = [l for l in text.splitlines() if not noise_pattern.match(l)]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()

    if not text:
        return "", title

    # Score paragraphs: keep substantive ones and headings
    result_paras = []
    chars_used = 0
    for para in re.split(r"\n{2,}", text):
        if chars_used >= max_chars:
            break
        is_heading = para.strip().startswith("#")
        if _score_paragraph(para) > 0 or is_heading:
            result_paras.append(para)
            chars_used += len(para)

    content = "\n\n".join(result_paras).strip()

    # Final trim to max_chars at sentence boundary
    if len(content) > max_chars:
        truncated = content[:max_chars]
        last_period = truncated.rfind(".")
        content = truncated[: last_period + 1].strip() if last_period > max_chars * 0.5 else truncated.strip()

    return content, title


def scrape_page_context(api_key: str, url: str, max_chars: int = 10000, mode: str = "default") -> dict:
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

    remove_selector = _COLLECTION_REMOVE_SELECTOR if mode == "ecommerce_collection" else _REMOVE_SELECTOR
    headers = {
        "Accept": "text/plain",
        "X-Return-Format": "markdown",
        "X-With-Links-Summary": "false",
        "X-With-Images-Summary": "false",
        "X-Remove-Selector": remove_selector,
        "X-No-Cache": "true",   # always fetch live page, never serve stale cached snapshot
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

        if mode == "ecommerce_collection":
            content, title = _build_collection_context(text, max_chars)
            if not content or content == "COLLECTION CONTEXT":
                return {"content": "", "title": title, "success": False,
                        "error": "No collection products, filters, or content found"}
            return {"content": content, "title": title, "success": True, "error": ""}

        # Default mode: standard page scraping
        content, title = _process_default_text(text, max_chars, _NOISE_LINE_PATTERNS)

        # If content is very short the X-Remove-Selector may have stripped the
        # site's main content container (e.g. a div with class*='navigation').
        # Retry once without it to recover the full page text.
        _CONTENT_MIN_CHARS = 300
        if len(content) < _CONTENT_MIN_CHARS and "X-Remove-Selector" in headers:
            try:
                headers_clean = {k: v for k, v in headers.items() if k != "X-Remove-Selector"}
                resp2 = requests.get(f"{JINA_BASE}/{url}", headers=headers_clean, timeout=35)
                if resp2.status_code == 200 and resp2.text.strip():
                    content2, title2 = _process_default_text(resp2.text.strip(), max_chars, _NOISE_LINE_PATTERNS)
                    if len(content2) > len(content):
                        content = content2
                        title = title2 or title
            except Exception:
                pass  # keep original content if retry fails

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
