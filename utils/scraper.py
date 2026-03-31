import re
import requests

JINA_BASE = "https://r.jina.ai"


def scrape_page_context(api_key: str, url: str, max_chars: int = 2000) -> dict:
    """Scrape a page via Jina Reader and return truncated topic context.

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
        "X-Return-Format": "text",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.get(
            f"{JINA_BASE}/{url}",
            headers=headers,
            timeout=30
        )
        resp.raise_for_status()

        text = resp.text.strip()

        if not text:
            return {"content": "", "title": "", "success": False, "error": "Jina returned empty content"}

        # Extract title from first line if it looks like a heading
        title = ""
        lines = text.splitlines()
        if lines and lines[0].startswith("Title:"):
            title = lines[0].replace("Title:", "").strip()

        # Clean up excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

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
