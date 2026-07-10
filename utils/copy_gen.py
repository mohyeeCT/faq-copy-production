import re
import json

_last_parse_error = ""
_last_batch_errors = {}


def get_last_parse_error() -> str:
    return _last_parse_error


def get_last_batch_errors() -> dict:
    return dict(_last_batch_errors)


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
        "fit, materials, use cases, and product selection. Do not create policy, shipping, return, "
        "availability, pricing, or warranty FAQs."
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


_UNSUPPORTED_CLAIM_GUARDRAIL = (
    "UNSUPPORTED CLAIM RULES:\n"
    "- Do not generate FAQ questions or answers about return, shipping, delivery, warranty, guarantee, "
    "eligibility, refund, exchange, availability, stock, pricing, discount, compliance, legal, medical, "
    "safety, or performance claims.\n"
    "- Exclude these topics entirely, even if they appear in PAA, AI Overview, scraped page content, "
    "or generic ecommerce expectations.\n"
    "- Prefer not to reference shipping or returns. Only use shipping or returns information when brand "
    "guidelines explicitly provide the exact policy details to use.\n"
    "- Do not use PAA, AI Overview, scraped page content, or generic ecommerce assumptions as source data "
    "for shipping or returns.\n"
    "- Treat AI Overview and PAA as research signals, not proof of this business's actual policies, "
    "inventory, pricing, warranties, guarantees, or eligibility rules.\n"
    "- Do not use neutral fallback wording for these topics.\n"
    "- Do not tell readers to check the policy page, contact customer service, review terms, or confirm "
    "availability, pricing, shipping, returns, refunds, exchanges, warranties, guarantees, or eligibility.\n"
    "- Replace risky policy or claim questions with safer page-specific questions about product purpose, "
    "features, materials, fit considerations, compatibility, use cases, care, selection, or comparisons."
)


_ECOMMERCE_COLLECTION_GUARDRAIL = (
    "ECOMMERCE COLLECTION CONTEXT RULES:\n"
    "- Use ecommerce collection context as research only to understand the page theme, shopper intent, "
    "product range, comparison factors, and common attributes.\n"
    "- Do not mention exact prices, sale prices, price ranges, or currency amounts from scraped products.\n"
    "- Do not mention exact product counts or imply a fixed number of products in the collection.\n"
    "- Do not mention exact sizes, filter values, inventory levels, SKU details, or availability claims.\n"
    "- Do not mention exact variant counts or imply a fixed number of variants.\n"
    "- Do not quote exact product names from the scraped collection unless the target keyword or page H1 "
    "is clearly about that single product.\n"
    "- If you reference specific colors, sizes, patterns, styles, or prices from the scraped data, always "
    "frame them as examples using inclusive language such as 'including X and other colors' or "
    "'sizes such as X and more.' Never present scraped values as a complete or exhaustive list.\n"
    "- Generalize collection details into stable buyer-focused ideas, such as multiple styles, different "
    "price points, available size options, material choices, use cases, or ways to compare products."
)


_PRODUCT_NAME_REPETITION_GUARDRAIL = (
    "PRODUCT NAME REPETITION RULE:\n"
    "- Do not repeat the exact product name more than 2 times total across all FAQ questions and answers "
    "for a specific product page.\n"
    "- Do not use partial product-name variations, shortened halves of the product name, or repeated brand/product fragments "
    "unless the phrase is the generic item or category the product represents.\n"
    "- Use natural references like this product, this item, this style, this option, or the category name after the product "
    "has been clearly introduced.\n"
    "- Keep the copy specific, but avoid making every question and answer start with or repeat the same exact product name "
    "or a near-duplicate variation."
)


_MAIN_KEYWORD_USAGE_GUARDRAIL = (
    "MAIN KEYWORD USAGE RULE:\n"
    "- Use the main keyword naturally no more than 1 to 2 times total across all FAQ questions and answers "
    "for that page.\n"
    "- Do not force the exact keyword into every question or answer.\n"
    "- After the keyword is introduced, use natural phrasing, pronouns, category terms, or page-specific context "
    "instead of repeating the same keyword."
)


def _is_ecommerce_collection_context(business_type: str, page_type: str, page_context: str = "") -> bool:
    business_type_norm = (business_type or "").strip().lower()
    page_type_norm = (page_type or "").strip().lower()
    if business_type_norm != "ecommerce":
        return False
    return (
        "category" in page_type_norm
        or "collection" in page_type_norm
        or "COLLECTION CONTEXT" in (page_context or "")
    )


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
    brand_guidelines: str = "",
) -> str:
    biz_ctx = _BIZ_CONTEXT.get(business_type, _BIZ_CONTEXT["general"])
    brand_line = f"Brand name: '{brand_name}'. Use exact casing throughout." if brand_name else "No brand name required."
    h1_line = f"Page H1 (context only, do not copy verbatim): {h1}" if h1 else ""
    forbidden_line = f"Never use these phrases: {forbidden_phrases}" if forbidden_phrases.strip() else ""
    brand_guidelines_block = f"BRAND & COPY GUIDELINES:\n{brand_guidelines.strip()}" if brand_guidelines.strip() else ""
    collection_guardrail = (
        _ECOMMERCE_COLLECTION_GUARDRAIL
        if _is_ecommerce_collection_context(business_type, page_type, page_context)
        else ""
    )

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
{brand_guidelines_block}
{_UNSUPPORTED_CLAIM_GUARDRAIL}
{_PRODUCT_NAME_REPETITION_GUARDRAIL}
{_MAIN_KEYWORD_USAGE_GUARDRAIL}
{collection_guardrail}

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
- Where possible, avoid repeating question patterns already used on other pages
- Do not create FAQs that repeat what the page copy already covers too closely
- Do not create FAQs that feel redundant with existing copy unless the FAQ format adds clear value
- Only keep FAQ ideas that fit naturally with the page and fill a real gap or improve clarity
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
    """Parse JSON array from AI response. Strips markdown fences if present.
    Attempts partial recovery if JSON is truncated mid-response.
    """
    global _last_parse_error
    _last_parse_error = ""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```\s*$", "", raw)
    raw = raw.strip()
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        _last_parse_error = f"FAQ JSON parse failed: expected array, got {type(data).__name__}"
        return []
    except Exception as e:
        _last_parse_error = f"FAQ JSON parse failed: {e}"
        # Attempt partial recovery: find the last complete object in the array.
        # Useful when max_tokens cuts off the response mid-JSON.
        try:
            last_bracket = raw.rfind('},')
            if last_bracket > 0:
                partial = raw[:last_bracket + 1] + ']'
                data = json.loads(partial)
                if isinstance(data, list) and data:
                    return data
        except Exception:
            pass
        return []


# ── Provider routing ──────────────────────────────────────────────────────────

# Default models for each provider (matched with SaaS backend for consistency)
DEFAULT_MODELS = {
    "Claude": "claude-sonnet-5",
    "OpenAI": "gpt-5.5",
    "Gemini (free)": "gemini-3.5-flash",
}

# Provider max_tokens defaults (single-page generation)
_PROVIDER_MAX_TOKENS = {
    "Claude": 16384,
    "OpenAI": 16384,
    "Gemini (free)": 4096,
}

# Batch-specific max_tokens ceiling — higher than single-page to prevent truncation
# on large batches. Only pay for tokens actually used; this is just a safety cap.
# Claude/OpenAI: 100k (well within 200k/128k context limits)
# Gemini: 8192 to keep free-tier batch responses bounded.
_BATCH_MAX_TOKENS = {
    "Claude": 100000,
    "OpenAI": 100000,
    "Gemini (free)": 8192,
}


def _extract_anthropic_text(content) -> str:
    text = "\n".join(
        str(block.text)
        for block in (content or [])
        if getattr(block, "type", "text") == "text" and getattr(block, "text", None)
    ).strip()
    if not text:
        raise RuntimeError("AI provider returned an empty text response")
    return text


def _anthropic_request_options(model: str, max_tokens: int) -> dict:
    options = {"model": model, "max_tokens": max_tokens}
    if (model or "").startswith("claude-sonnet-5"):
        options["extra_body"] = {"thinking": {"type": "disabled"}}
    return options


def _openai_token_limit(model: str, max_tokens: int) -> dict:
    if (model or "").startswith("gpt-5"):
        return {"max_completion_tokens": max_tokens}
    return {"max_tokens": max_tokens}


def _call_claude(api_key: str, prompt: str, max_tokens: int = 16384, model: str = None) -> str:
    import anthropic
    if model is None:
        model = DEFAULT_MODELS["Claude"]
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        **_anthropic_request_options(model, max_tokens),
        messages=[{"role": "user", "content": prompt}]
    )
    return _extract_anthropic_text(msg.content)


def _call_openai(api_key: str, prompt: str, max_tokens: int = 16384, model: str = None) -> str:
    from openai import OpenAI
    if model is None:
        model = DEFAULT_MODELS["OpenAI"]
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        **_openai_token_limit(model, max_tokens),
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content


def _call_gemini(api_key: str, prompt: str, max_tokens: int = 4096, model: str = None) -> str:
    from google import genai
    if model is None:
        model = DEFAULT_MODELS["Gemini (free)"]
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=model,
        contents=prompt
    )
    return resp.text


_PROVIDER_FN = {
    "Claude": _call_claude,
    "OpenAI": _call_openai,
    "Gemini (free)": _call_gemini,
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
    brand_guidelines: str = "",
    include_brand: bool = True,
    model: str = None,
) -> list:
    """Generate FAQ Q&A pairs using the selected AI provider.

    Returns a list of dicts: [{"question": str, "answer": str, "source": str}, ...]
    source: "ai_overview" | "paa" | "generated"
    Raises on API failure so callers can handle and log errors.
    """
    fn = _PROVIDER_FN.get(provider)
    if not fn:
        raise ValueError(f"Unknown provider: {provider}")

    effective_brand = brand_name if include_brand else ""
    prompt = _build_prompt(
        keyword=keyword,
        page_type=page_type,
        brand_name=effective_brand,
        business_type=business_type,
        h1=h1,
        ai_overview_sections=ai_overview_sections,
        ai_overview_raw=ai_overview_raw,
        paa_items=paa_items,
        num_faqs=num_faqs,
        forbidden_phrases=forbidden_phrases,
        page_context=page_context,
        used_question_patterns=used_question_patterns,
        brand_guidelines=brand_guidelines,
    )

    # Use provider-specific max_tokens
    max_tokens = _PROVIDER_MAX_TOKENS.get(provider, 8192)
    raw = fn(api_key, prompt, max_tokens=max_tokens, model=model)
    items = _parse_faq_json(raw)

    sanitised = []
    for item in items:
        if not isinstance(item, dict):
            continue
        sanitised.append({
            "question": sanitise(item.get("question", ""), effective_brand),
            "answer": sanitise(item.get("answer", ""), effective_brand),
            "source": item.get("source", "generated"),
        })

    return sanitised


_last_batch_page_blocks: list = []  # stores per-page prompt blocks from last batch call

def _build_batch_prompt(pages: list, num_faqs: int) -> str:
    """Build a single prompt for multiple pages grouped by category.

    Each page dict contains:
        keyword, page_type, brand_name, business_type, h1,
        ai_overview_sections, ai_overview_raw, paa_items,
        page_context, forbidden_phrases, used_question_patterns
    """
    blocks = []

    for i, p in enumerate(pages, start=1):
        biz_ctx = _BIZ_CONTEXT.get(p.get("business_type", "general"), _BIZ_CONTEXT["general"])
        keyword = p.get("keyword", "")
        h1 = p.get("h1", "")
        brand_name = p.get("brand_name", "")
        page_context = p.get("page_context", "")
        ao_sections = p.get("ai_overview_sections", [])
        paa_items = p.get("paa_items", [])
        forbidden = p.get("forbidden_phrases", "")
        used_patterns = p.get("used_question_patterns", [])

        brand_line = f"Brand name: '{brand_name}'. Use exact casing." if brand_name else ""
        h1_line = f"H1: {h1}" if h1 else ""
        forbidden_line = f"Never use: {forbidden}" if forbidden.strip() else ""
        brand_guidelines = p.get("brand_guidelines", "")
        brand_guidelines_block = f"BRAND & COPY GUIDELINES:\n{brand_guidelines.strip()}" if brand_guidelines.strip() else ""
        collection_guardrail = (
            _ECOMMERCE_COLLECTION_GUARDRAIL
            if _is_ecommerce_collection_context(
                p.get("business_type", ""),
                p.get("page_type", ""),
                page_context,
            )
            else ""
        )

        ctx = f"Page content:\n---\n{page_context}\n---" if page_context else ""

        if ao_sections:
            ao_text = "\n".join(
                f"- {s['content']}" if s.get("content") else f"- {s.get('title', '')}"
                for s in ao_sections
            )
            ao_block = f"AI Overview:\n{ao_text}"
        else:
            ao_block = "AI Overview: not available"

        if paa_items:
            paa_lines = []
            for p2 in paa_items[:num_faqs + 3]:
                line = f"- Q: {p2['question']}"
                if p2.get("answer"):
                    line += f" | A: {p2['answer'][:100]}"
                paa_lines.append(line)
            paa_block = "PAA:\n" + "\n".join(paa_lines)
        else:
            paa_block = "PAA: not available"

        if used_patterns:
            patterns = "\n".join(f"- {p3}" for p3 in used_patterns[:15])
            used_block = f"Avoid repeating these question patterns from other pages where possible:\n{patterns}"
        else:
            used_block = ""

        block = f"""--- PAGE {i} ---
Keyword: {keyword}
Page type: {p.get("page_type", "general")}
Business type: {biz_ctx}
{h1_line}
{brand_line}
{forbidden_line}
{brand_guidelines_block}
{_UNSUPPORTED_CLAIM_GUARDRAIL}
{collection_guardrail}

{ctx}

{ao_block}

{paa_block}

{used_block}"""
        blocks.append(block.strip())

    pages_text = "\n\n".join(blocks)

    # Also return individual page blocks for per-page debug display
    global _last_batch_page_blocks
    _last_batch_page_blocks = blocks  # overwritten each call

    return f"""You are an expert SEO copywriter. Generate FAQ content for {len(pages)} web pages listed below.

For each page, generate exactly {num_faqs} FAQ questions that real visitors would ask about THAT SPECIFIC PAGE.

Rules for all pages:
- Focus on what is unique and specific to each page — not generic questions that apply to every page in the category
- Where pages are similar products, vary the questions to highlight different aspects of each
- Lead each answer with a direct, complete response in the first sentence
- Keep answers 40 to 80 words, written for featured snippet format
- Use AI Overview sections as priority 1 signal, PAA as priority 2, page content as fallback
- Only use AIO/PAA questions if genuinely relevant to that specific page
- No em dashes. No filler openers ("Great question", "Certainly", "Of course", "Absolutely")
- Where possible, avoid repeating question patterns already used on other pages
- Do not create FAQs that repeat what the page copy already covers too closely
- Do not create FAQs that feel redundant with existing copy unless the FAQ format adds clear value
- Only keep FAQ ideas that fit naturally with the page and fill a real gap or improve clarity
{_PRODUCT_NAME_REPETITION_GUARDRAIL}
{_MAIN_KEYWORD_USAGE_GUARDRAIL}

{pages_text}

Return a JSON object with one key per page index (1-based). Each value is an array of {num_faqs} FAQ items:
{{
  "1": [{{"question": "...", "answer": "...", "source": "ai_overview|paa|generated"}}, ...],
  "2": [{{"question": "...", "answer": "...", "source": "..."}}, ...],
  ...
}}

Return only the raw JSON object. No preamble, no markdown code fences."""


def _parse_batch_json(raw: str, num_pages: int) -> dict:
    """Parse batch JSON response. Returns dict keyed by string page index."""
    global _last_parse_error
    _last_parse_error = ""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```\s*$", "", raw)
    raw = raw.strip()
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
        _last_parse_error = f"Batch FAQ JSON parse failed: expected object, got {type(data).__name__}"
    except Exception as e:
        _last_parse_error = f"Batch FAQ JSON parse failed: {e}"
    # Return empty dicts for all pages on failure
    return {str(i): [] for i in range(1, num_pages + 1)}


def generate_faq_batch(
    provider: str,
    api_key: str,
    pages: list,
    num_faqs: int,
    include_brand: bool = True,
    model: str = None,
) -> tuple:
    """Generate FAQs for multiple pages in a single AI call.

    Returns (results, prompt_sent, page_debug_prompts):
        results: dict keyed by 0-based index -> list of faq dicts
        prompt_sent: full prompt string sent to the AI
        page_debug_prompts: dict keyed by 0-based index -> per-page context summary for debug
    """
    fn = _PROVIDER_FN.get(provider)
    if not fn:
        raise ValueError(f"Unknown provider: {provider}")

    global _last_batch_errors
    _last_batch_errors = {}

    prompt = _build_batch_prompt(pages, num_faqs)
    # Scale tokens: ~400 per FAQ × num_faqs × pages, capped at batch-specific provider max
    safe_max = _BATCH_MAX_TOKENS.get(provider, 64000)
    batch_max_tokens = min(safe_max, max(2048, len(pages) * num_faqs * 400))
    raw = fn(api_key, prompt, max_tokens=batch_max_tokens, model=model)
    parsed = _parse_batch_json(raw, len(pages))

    # Build per-page debug summaries showing exactly what context the AI received
    page_debug_prompts = {}
    for i, page in enumerate(pages):
        biz_ctx = _BIZ_CONTEXT.get(page.get("business_type", "general"), _BIZ_CONTEXT["general"])
        ao_sections = page.get("ai_overview_sections", [])
        paa_items_p = page.get("paa_items", [])
        used = page.get("used_question_patterns", [])

        ao_text = ("\n".join(
            f"- {s.get('content', s.get('title', ''))}" for s in ao_sections
        ) if ao_sections else "Not available")

        paa_text = ("\n".join(
            f"- Q: {p['question']}" + (f"\n  A: {p['answer'][:120]}" if p.get("answer") else "")
            for p in paa_items_p[:8]
        ) if paa_items_p else "Not available")

        used_text = ("\n".join(f"- {u}" for u in used[:15]) if used else "None")

        ctx = page.get("page_context", "") or "Not scraped"

        page_debug_prompts[i] = (
            f"=== SIGNALS SENT TO AI ===\n\n"
            f"KEYWORD: {page.get('keyword', '')}\n"
            f"PAGE TYPE: {page.get('page_type', '')}\n"
            f"BUSINESS TYPE: {biz_ctx}\n"
            f"H1: {page.get('h1', '') or 'not provided'}\n"
            f"BRAND: {page.get('brand_name', '') or 'not provided'}\n\n"
            f"--- PAGE CONTENT EXCERPT ---\n{ctx}\n\n"
            f"--- AI OVERVIEW ---\n{ao_text}\n\n"
            f"--- PEOPLE ALSO ASK ---\n{paa_text}\n\n"
            f"--- USED QUESTION PATTERNS (avoid) ---\n{used_text}"
        )

    results = {}
    for i, page in enumerate(pages):
        brand_name = page.get("brand_name", "") if include_brand else ""
        raw_items = parsed.get(str(i + 1), [])
        sanitised = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            sanitised.append({
                "question": sanitise(item.get("question", ""), brand_name),
                "answer": sanitise(item.get("answer", ""), brand_name),
                "source": item.get("source", "generated"),
            })

        # Fallback: if batch parsing returned nothing for this page, retry solo
        if not sanitised:
            try:
                solo_prompt = _build_batch_prompt([page], num_faqs)
                solo_max_tokens = _PROVIDER_MAX_TOKENS.get(provider, 8192)
                solo_raw = fn(api_key, solo_prompt, max_tokens=solo_max_tokens, model=model)
                solo_parsed = _parse_batch_json(solo_raw, 1)
                for item in (solo_parsed.get("1") or []):
                    if not isinstance(item, dict):
                        continue
                    sanitised.append({
                        "question": sanitise(item.get("question", ""), brand_name),
                        "answer": sanitise(item.get("answer", ""), brand_name),
                        "source": item.get("source", "generated"),
                    })
            except Exception as e:
                _last_batch_errors[i] = f"Solo fallback failed: {e}"

        results[i] = sanitised

    for i, error in _last_batch_errors.items():
        page_debug_prompts[i] = (
            page_debug_prompts.get(i, "")
            + f"\n\n--- BATCH FALLBACK ERROR ---\n{error}"
        )

    return results, prompt, page_debug_prompts
