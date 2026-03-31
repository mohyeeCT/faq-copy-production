import re
import requests
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Tags that are noise and should be stripped before text extraction
_STRIP_TAGS = [
    "nav", "header", "footer", "aside", "form",
    "script", "style", "noscript", "iframe",
    "svg", "figure", "picture",
    "[document]", "head"
]

# CSS classes/ids that indicate nav or boilerplate (substring match)
_NOISE_CLASSES = [
    "nav", "menu", "header", "footer", "sidebar", "breadcrumb",
    "cookie", "banner", "popup", "modal", "overlay",
    "social", "share", "newsletter", "subscribe",
    "related", "recommended", "advertisement", "ad-",
]


def _is_noise_element(tag) -> bool:
    classes = " ".join(tag.get("class", []))
    tag_id = tag.get("id", "")
    combined = (classes + " " + tag_id).lower()
    return any(n in combined for n in _NOISE_CLASSES)


def scrape_page_context(url: str, max_chars: int = 2000) -> dict:
    """Scrape a page with requests + BeautifulSoup and return truncated topic context.

    No API key required.

    Returns:
        {
            "content": str,
            "title": str,
            "success": bool,
            "error": str
        }
    """
    if not url:
        return {"content": "", "title": "", "success": False, "error": "No URL provided"}

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=20, allow_redirects=True)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Remove noise tags entirely
        for tag_name in _STRIP_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Remove noise elements by class/id
        for tag in soup.find_all(True):
            if _is_noise_element(tag):
                tag.decompose()

        # Try to find main content container first
        main = (
            soup.find("main") or
            soup.find(attrs={"role": "main"}) or
            soup.find("article") or
            soup.find(id=re.compile(r"content|main|body", re.I)) or
            soup.find(class_=re.compile(r"content|main|body|post|entry", re.I)) or
            soup.body
        )

        if not main:
            return {"content": "", "title": title, "success": False, "error": "Could not find main content element"}

        # Extract text
        text = main.get_text(separator="\n", strip=True)

        # Clean up whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = text.strip()

        if not text:
            return {"content": "", "title": title, "success": False, "error": "Page returned no extractable text"}

        # Take first ~50%, capped at max_chars
        total_len = len(text)
        cutoff = min(max_chars, total_len // 2 + 1)
        truncated = text[:cutoff]

        # Cut at last sentence boundary
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
        return {"content": "", "title": "", "success": False, "error": "Request timed out"}
    except requests.exceptions.HTTPError as e:
        return {"content": "", "title": "", "success": False, "error": f"HTTP {e.response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"content": "", "title": "", "success": False, "error": str(e)}
    except Exception as e:
        return {"content": "", "title": "", "success": False, "error": str(e)}
