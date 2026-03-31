import requests
import re

FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v1/scrape"

# Noise patterns to strip before passing content to AI
_NOISE_PATTERNS = [
    r"(?i)(nav|navigation|menu|header|footer|sidebar|breadcrumb|cookie|privacy policy"
    r"|terms of service|subscribe|newsletter|follow us|social media"
    r"|copyright|all rights reserved)[\s\S]{0,200}",
]


def scrape_page_context(api_key: str, url: str, max_chars: int = 2000) -> dict:
    """Scrape a page using FireCrawl and return a truncated topic context string.

    Returns:
        {
            "content": str,   # truncated markdown ready for prompt injection
            "title": str,     # page title if found
            "success": bool,
            "error": str      # populated only on failure
        }
    """
    if not api_key or not url:
        return {"content": "", "title": "", "success": False, "error": "Missing API key or URL"}

    try:
        resp = requests.post(
            FIRECRAWL_SCRAPE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": True,   # strips nav, footer, ads automatically
                "excludeTags": ["nav", "footer", "header", "aside", "form",
                                "script", "style", "noscript", "iframe"],
                "timeout": 30000
            },
            timeout=45
        )
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            return {
                "content": "", "title": "", "success": False,
                "error": data.get("error", "FireCrawl returned success=false")
            }

        markdown = data.get("data", {}).get("markdown", "") or ""
        title = data.get("data", {}).get("metadata", {}).get("title", "") or ""

        # Strip any remaining nav/footer noise
        cleaned = markdown
        for pattern in _NOISE_PATTERNS:
            cleaned = re.sub(pattern, " ", cleaned)

        # Collapse whitespace
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = cleaned.strip()

        # Take first ~50% of content, capped at max_chars
        total_len = len(cleaned)
        cutoff = min(max_chars, total_len // 2 + 1)
        truncated = cleaned[:cutoff]

        # Don't cut mid-sentence
        last_period = truncated.rfind(".")
        if last_period > cutoff * 0.6:
            truncated = truncated[: last_period + 1]

        return {
            "content": truncated.strip(),
            "title": title,
            "success": True,
            "error": ""
        }

    except requests.exceptions.Timeout:
        return {"content": "", "title": "", "success": False, "error": "FireCrawl request timed out"}
    except requests.exceptions.RequestException as e:
        return {"content": "", "title": "", "success": False, "error": str(e)}
    except Exception as e:
        return {"content": "", "title": "", "success": False, "error": str(e)}
