import re
import json


# ── Sanitiser ────────────────────────────────────────────────────────────────

def sanitise(text: str, brand_name: str = "") -> str:
    """Strip em dashes, fix brand casing, remove surrounding quotes."""
    if not text:
        return ""
    text = text.replace("\u2014", " ").replace("\u2013", " ")
    text = text.strip().strip('"').strip("'").strip()
    if brand_name:
        text = re.sub(re.escape(brand_name), brand_name, text, flags=re.IGNORECASE)
    return text


# ── Schema builder ────────────────────────────────────────────────────────────

def build_faq_schema(faq_items: list, page_url: str = "") -> str:
    """Generate a schema.org FAQPage JSON-LD script block ready to paste into <head>.

    Args:
        faq_items: list of {"question": str, "answer": str}
        page_url: optional, not required by spec but useful for reference

    Returns:
        Full <script type="application/ld+json"> block as a string.
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item["answer"]
                }
            }
            for item in faq_items
            if item.get("question") and item.get("answer")
        ]
    }

    json_str = json.dumps(schema, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{json_str}\n</script>'


# ── Prompt builder ────────────────────────────────────────────────────────────

_BIZ_CONTEXT = {
    "b2b": (
        "This is a B2B page. Answers should be professional, solution-focused, and concise. "
        "No consumer CTAs. Focus on ROI, process, and expertise."
    ),
    "b2c": (
        "This is a B2C page. Answers can be conversational. Include a light CTA where it fits naturally."
    ),
    "ecommerce": (
        "This is an ecommerce page. Answers should address buying concerns, specs, compatibility, "
        "shipping, and returns."
    ),
    "service": (
        "This is a service page. Answers should build trust, clarify process, and highlight expertise."
    ),
    "local": (
        "This is a local business page. Answers should address local context, service area, "
        "and proximity where relevant."
    ),
    "general": "Write for a general audience. Keep answers clear and helpful.",
}


def _build_prompt(
    keyword: str,
    page_type: str,
    brand_name: str,
    business_type: str,
    h1: str,
    paa_questions: list,
    num_faqs: int,
    forbidden_phrases: str,
    page_context: str,
) -> str:
    biz_ctx = _BIZ_CONTEXT.get(business_type, _BIZ_CONTEXT["general"])
    brand_line = f"Brand name: '{brand_name}'. Use exact casing throughout." if brand_name else "No brand name required."
    h1_line = f"Page H1 (context only, do not copy verbatim): {h1}" if h1 else ""
    forbidden_line = f"Never use these phrases: {forbidden_phrases}" if forbidden_phrases.strip() else ""

    if page_context:
        context_block = (
            "PAGE CONTENT EXCERPT (use this to understand what the page is actually about "
            "and ensure FAQs are relevant to the page topic, not just the keyword):\n"
            f"---\n{page_context}\n---"
        )
    else:
        context_block = ""

    if paa_questions:
        q_list = "\n".join(f"- {q}" for q in paa_questions[:num_faqs + 3])
        seed_block = (
            f"Use these People Also Ask questions as seed questions. "
            f"You may rephrase slightly for clarity or to better fit the page topic. "
            f"If fewer than {num_faqs} are listed, generate the remaining ones based on "
            f"the page content, keyword, and common user intent.\n"
            f"{q_list}"
        )
    else:
        seed_block = (
            f"No PAA data available. Generate {num_faqs} relevant FAQ questions based on "
            f"the page content excerpt, keyword, and common user intent."
        )

    return f"""You are an expert SEO copywriter writing FAQ content for a web page.

Target keyword: {keyword}
Page type: {page_type}
Business type context: {biz_ctx}
{h1_line}
{brand_line}
{forbidden_line}

{context_block}

{seed_block}

Rules:
- FAQs must reflect the actual content and topic of the page, not generic keyword answers
- Each answer must be 40 to 80 words
- No em dashes anywhere in questions or answers
- No filler openers: never start with "Great question", "Certainly", "Of course", "Absolutely"
- Answers must be factual and directly address the question
- Do not pad with generic advice unrelated to the page
- Questions should reflect real search intent, not marketing copy

Return EXACTLY {num_faqs} FAQ items as a JSON array:
[
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}}
]

Return only the raw JSON array. No preamble, no explanation, no markdown code fences."""


def _parse_faq_json(raw: str) -> list:
    """Parse JSON array from AI response. Strips markdown fences if present."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```\s*$", "", raw)
    raw = raw.strip()
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


# ── Provider routing ──────────────────────────────────────────────────────────

def _call_claude(api_key: str, prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text


def _call_openai(api_key: str, prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content


def _call_gemini(api_key: str, prompt: str) -> str:
    from google import genai
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return resp.text


def _call_mistral(api_key: str, prompt: str) -> str:
    from mistralai.client import Mistral
    client = Mistral(api_key=api_key)
    resp = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content


def _call_groq(api_key: str, prompt: str) -> str:
    from groq import Groq
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model="llama3-70b-8192",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content


_PROVIDER_FN = {
    "Claude": _call_claude,
    "OpenAI": _call_openai,
    "Gemini (free)": _call_gemini,
    "Mistral (free tier)": _call_mistral,
    "Groq (free tier)": _call_groq,
}


# ── Public entry point ────────────────────────────────────────────────────────

def generate_faq(
    provider: str,
    api_key: str,
    keyword: str,
    page_type: str,
    brand_name: str,
    business_type: str,
    h1: str,
    paa_questions: list,
    num_faqs: int,
    forbidden_phrases: str = "",
    page_context: str = "",
) -> list:
    """Generate FAQ Q&A pairs using the selected AI provider.

    Returns a list of dicts: [{"question": str, "answer": str}, ...]
    All output is run through the sanitiser.
    Raises on API failure so callers can handle and log errors.
    """
    fn = _PROVIDER_FN.get(provider)
    if not fn:
        raise ValueError(f"Unknown provider: {provider}")

    prompt = _build_prompt(
        keyword=keyword,
        page_type=page_type,
        brand_name=brand_name,
        business_type=business_type,
        h1=h1,
        paa_questions=paa_questions,
        num_faqs=num_faqs,
        forbidden_phrases=forbidden_phrases,
        page_context=page_context,
    )

    raw = fn(api_key, prompt)
    items = _parse_faq_json(raw)

    sanitised = []
    for item in items:
        if not isinstance(item, dict):
            continue
        sanitised.append({
            "question": sanitise(item.get("question", ""), brand_name),
            "answer": sanitise(item.get("answer", ""), brand_name),
        })

    return sanitised
