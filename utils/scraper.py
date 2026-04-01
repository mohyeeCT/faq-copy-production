import re
import requests

JINA_BASE = "https://r.jina.ai"


def scrape_page_context(api_key: str, url: str, max_chars: int = 2000) -> dict:
    """Scrape a page via Jina Reader and return truncated topic context.

    Uses X-Target-Selector to focus on main content elements only,
    skipping nav, header, cart, and footer boilerplate.

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

    headers = {
        "Accept": "text/plain",
        "X-Return-Format": "markdown",
        "X-With-Links-Summary": "false",
        "X-With-Images-Summary": "false",
        # Target main content containers used by most CMSs and page builders.
        # Jina will extract only the first matching element.
        "X-Target-Selector": "main, #MainContent, #main-content, article, .page-content, .entry-content, .post-content, [role='main']",
        "X-Timeout": "30",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.get(
            f"{JINA_BASE}/{url}",
            headers=headers,
            timeout=35
        )
        resp.raise_for_status()

        text = resp.text.strip()

        if not text:
            return {"content": "", "title": "", "success": False, "error": "Jina returned empty content"}

        # Extract title from Jina metadata block (format: "Title: ...")
        title = ""
        title_match = re.search(r"^Title:\s*(.+)$", text, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()

        # Drop image lines
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

        # Drop pure link-list lines (nav remnants)
        text = re.sub(r"^\s*\*\s+\[.+?\]\(https?://.+?\)\s*$", "", text, flags=re.MULTILINE)

        # Collapse whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        if not text:
            return {"content": "", "title": title, "success": False, "error": "No content found after stripping boilerplate"}

        # Take first ~50% of cleaned content, capped at max_chars
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
