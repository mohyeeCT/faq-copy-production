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

def build_faq_schema(faq_items: list) -> tuple:
    """Generate a schema.org FAQPage JSON-LD block.

    Returns:
        (raw_json, script_block)
        raw_json     -- JSON string only, safe to store in Google Sheets
        script_block -- full <script> tag for pasting into <head>
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

    raw_json = json.dumps(schema, ensure_ascii=False, indent=2)
    script_block = '<script type="application/ld+json">\n' + raw_json + '\n</script>'
    return raw_json, script_block

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


def _fingerprint_question(question: str, keyword: str = "") -> str:
    """Strip keyword/brand and normalise a question to a pattern string.
    Used to detect structurally similar questions across different pages.
    e.g. "Does fierce fruit raspberry puree contain added sugar?" ->
         "does contain added sugar?"
    """
    import re
    q = question.lower().strip()
    # Remove the keyword words from the question
    if keyword:
        for word in re.findall(r"[a-z]+", keyword.lower()):
            if len(word) > 2:
                q = re.sub(r"\b" + re.escape(word) + r"\b", "", q)
    # Collapse whitespace
    q = re.sub(r"\s+", " ", q).strip()
    return q



def _build_prompt(
    keyword: str,
    page_type: str,
    brand_name: str,
    business_type: str,
    h1: str,
    ai_overview_sections: list,
    ai_overview_raw: str,
    paa_items: list,
    num_faqs: int,
    forbidden_phrases: str,
    page_context: str,
    used_question_patterns: list = None,
) -> str:
    biz_ctx = _BIZ_CONTEXT.get(business_type, _BIZ_CONTEXT["general"])
    brand_line = f"Brand name: '{brand_name}'. Use exact casing throughout." if brand_name else "No brand name required."
    h1_line = f"Page H1 (context only, do not copy verbatim): {h1}" if h1 else ""
    forbidden_line = f"Never use these phrases: {forbidden_phrases}" if forbidden_phrases.strip() else ""

    if page_context:
        context_block = (
            "PAGE CONTENT EXCERPT (use this to understand what the page is actually about):\n"
            f"---\n{page_context}\n---"
        )
    else:
        context_block = ""

    # Used question patterns from previous pages in this run
    if used_question_patterns:
        patterns_list = "\n".join(f"- {p}" for p in used_question_patterns[:20])
        used_block = (
            "QUESTION PATTERNS USED ON OTHER PAGES IN THIS RUN (try to avoid repeating these "
            "structural patterns where possible — but only if you can find a more specific or "
            "distinctive question for this page. Do not sacrifice relevance to avoid repetition):\n"
            + patterns_list
        )
    else:
        used_block = ""

    # ── AI Overview block (priority 1) ────────────────────────────────────
    if ai_overview_sections:
        ao_lines = []
        for s in ai_overview_sections:
            if s.get("title") and s.get("content"):
                ao_lines.append(f"- {s['title']}: {s['content']}")
            elif s.get("title"):
                ao_lines.append(f"- {s['title']}")
            elif s.get("content"):
                ao_lines.append(f"- {s['content']}")
        ao_block = (
            "GOOGLE AI OVERVIEW (highest priority signal — Google already surfaced these subtopics "
            "for this keyword. Mirror this structure in the FAQs to maximise AI Overview citation potential):\n"
            + "\n".join(ao_lines)
        )
    else:
        ao_block = "No AI Overview found for this keyword. Use PAA and page context as signals."

    # ── PAA block (priority 2) ────────────────────────────────────────────
    if paa_items:
        paa_lines = []
        for p in paa_items[:num_faqs + 3]:
            line = f"- Q: {p['question']}"
            if p.get("answer"):
                line += f" | Snippet: {p['answer'][:120]}"
            paa_lines.append(line)
        paa_block = (
            "PEOPLE ALSO ASK (use these to fill gaps not already covered by the AI Overview):\n"
            + "\n".join(paa_lines)
        )
    else:
        paa_block = "No PAA data available."

    used_block_str = f"\n{used_block}\n" if used_block else ""

    return f"""You are an expert SEO copywriter writing FAQ content for a web page. Your job is to generate questions that real buyers or visitors would ask about THIS SPECIFIC PAGE, then answer them in a way that could rank in Google AI Overviews.

Target keyword: {keyword}
Page type: {page_type}
Business type context: {biz_ctx}
{h1_line}
{brand_line}
{forbidden_line}

{context_block}

{ao_block}

{paa_block}
{used_block_str}
YOUR TASK:
Generate {num_faqs} FAQ questions that are directly relevant to this specific page and keyword. Use the AI Overview and PAA data above as research signals to understand what users want to know — but do NOT copy or rephrase those questions verbatim. Only use a PAA or AI Overview question if it is genuinely relevant to what this page is about.

For each question:
- Focus on what is UNIQUE and SPECIFIC to this product or page — not questions that would apply equally to any product in the same category (e.g. avoid generic shipping, allergen, or storage questions unless the page has truly distinctive information about them)
- It must relate directly to the page content, keyword, and what a visitor to this page would actually want to know
- Reject any signal question that is too generic, off-topic, or does not match the page purpose
- Where possible, avoid repeating question patterns already used on other pages in this run — but only if a more specific alternative exists for this page
- Lead the answer with a direct, complete response in the first sentence
- Keep answers 40 to 80 words, written for featured snippet format
- No em dashes. No filler openers (never: "Great question", "Certainly", "Of course", "Absolutely")

Return EXACTLY {num_faqs} FAQ items as a JSON array with a "source" field:
[
  {{"question": "...", "answer": "...", "source": "ai_overview"}},
  {{"question": "...", "answer": "...", "source": "paa"}},
  {{"question": "...", "answer": "...", "source": "generated"}}
]

source values: "ai_overview" if inspired by the AI Overview, "paa" if inspired by PAA, "generated" if neither. If a PAA/AI Overview question was rejected as irrelevant, use "generated" for the replacement.
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
    ai_overview_sections: list,
    ai_overview_raw: str,
    paa_items: list,
    num_faqs: int,
    forbidden_phrases: str = "",
    page_context: str = "",
    used_question_patterns: list = None,
) -> list:
    """Generate FAQ Q&A pairs using the selected AI provider.

    Returns a list of dicts: [{"question": str, "answer": str, "source": str}, ...]
    source: "ai_overview" | "paa" | "generated"
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
        ai_overview_sections=ai_overview_sections,
        ai_overview_raw=ai_overview_raw,
        paa_items=paa_items,
        num_faqs=num_faqs,
        forbidden_phrases=forbidden_phrases,
        page_context=page_context,
        used_question_patterns=used_question_patterns,
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
            "source": item.get("source", "generated"),
        })

    return sanitised
