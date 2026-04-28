import re
import requests

JINA_BASE = "https://r.jina.ai"

# Ordered selectors — Jina uses the first match.
# Shopify-specific selectors first, then generic fallbacks.
_CONTENT_SELECTORS = ", ".join([
    ".product__description",
    ".product-description",
    "[class*='product-description']",
    "[class*='product__description']",
    ".rte",
    ".product__info-container",
    "main",
    "#MainContent",
    "#main-content",
    "article",
    ".page-content",
    ".entry-content",
    ".post-content",
    "[role='main']",
])


def scrape_page_context(api_key: str, url: str, max_chars: int = 3000) -> dict:
    """Scrape a page via Jina Reader and return cleaned topic context.

    Uses X-Target-Selector to focus on product/main content.
    No 50% cutoff — Jina already strips nav/footer via the selector,
    so we take the first max_chars of whatever it returns.
    Falls back to no selector if the selector causes a 422.

    Returns:
        {"content": str, "title": str, "success": bool, "error": str}
    """
    if not url:
        return {"content": "", "title": "", "success": False, "error": "No URL provided"}

    def _make_request(with_selector: bool) -> requests.Response:
        hdrs = {
            "Accept": "text/plain",
            "X-Return-Format": "markdown",
            "X-With-Links-Summary": "false",
            "X-With-Images-Summary": "false",
            "X-Timeout": "30",
        }
        if api_key:
            hdrs["Authorization"] = f"Bearer {api_key}"
        if with_selector:
            hdrs["X-Target-Selector"] = _CONTENT_SELECTORS
        return requests.get(f"{JINA_BASE}/{url}", headers=hdrs, timeout=35)

    try:
        resp = _make_request(with_selector=True)

        # 422 means no selector matched — retry without selector
        if resp.status_code == 422:
            resp = _make_request(with_selector=False)

        resp.raise_for_status()
        text = resp.text.strip()

        if not text:
            return {"content": "", "title": "", "success": False, "error": "Jina returned empty content"}

        # Extract title from Jina metadata block
        title = ""
        title_match = re.search(r"^Title:\s*(.+)$", text, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()

        # Drop image lines
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

        # Drop pure nav link-list lines
        text = re.sub(r"^\s*\*\s+\[.+?\]\(https?://.+?\)\s*$", "", text, flags=re.MULTILINE)

        # Drop ecommerce noise: prices, cart buttons, availability text
        text = re.sub(
            r"^\s*(\$[\d,.]+[\s\S]{0,40}|Add to cart|Sold out|Sale price|Regular price"
            r"|Unit price|Quantity must be|Adding product|Please allow \d).*$",
            "", text, flags=re.MULTILINE | re.IGNORECASE
        )

        # Drop store location blocks (phone numbers, address lines, pickup text)
        text = re.sub(
            r"^\s*(\+?1?[\s\-.]?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}"
            r"|Pickup available|Usually ready|Check availability"
            r"|Service Center|\d{4,6}\s+\w+\s+(Road|Street|Ave|Blvd|Pkwy|Way|Place)).*$",
            "", text, flags=re.MULTILINE | re.IGNORECASE
        )

        # Collapse whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        if not text:
            return {"content": "", "title": title, "success": False,
                    "error": "No content found after stripping boilerplate"}

        # Take first max_chars — no 50% cutoff needed
        truncated = text[:max_chars]

        # Avoid mid-sentence truncation
        if len(text) > max_chars:
            last_period = truncated.rfind(".")
            if last_period > max_chars * 0.5:
                truncated = truncated[: last_period + 1]

        return {"content": truncated.strip(), "title": title, "success": True, "error": ""}

    except requests.exceptions.Timeout:
        return {"content": "", "title": "", "success": False, "error": "Request timed out"}
    except requests.exceptions.HTTPError as e:
        return {"content": "", "title": "", "success": False, "error": f"HTTP {e.response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"content": "", "title": "", "success": False, "error": str(e)}
    except Exception as e:
        return {"content": "", "title": "", "success": False, "error": str(e)}
