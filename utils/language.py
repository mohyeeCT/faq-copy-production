import re
from collections.abc import Iterable


US_ENGLISH_OUTPUT_RULE = """
U.S. ENGLISH REQUIREMENT:
- Write all newly authored text in U.S. English, including spelling, grammar,
  punctuation, and idiom.
- Use U.S. forms such as color, organize, optimize, prioritize, and center.
- Do not imitate British spelling from scraped pages, search results, niche
  guidance, Brand Profile example copy, or other context.
- Preserve official brand and product names, URLs, direct quotations,
  testimonials, and any exact source material that another rule requires to
  remain verbatim.
""".strip()


CUSTOMER_FACING_OUTPUT_RULE = """
CUSTOMER-FACING SOURCE LANGUAGE RULE:
- Write only publication-ready, customer-facing copy.
- Use page content, search results, keywords, and brand guidance silently as
  grounding. Never describe, cite, or narrate the source material, supplied
  context, prompt, scraping, or research process.
- Do not write phrases such as "the live product page states," "the product
  page offers," "the page positions," "according to the provided context," or
  "the scraped content shows."
- Never expose internal research labels such as AI Overview, People Also Ask,
  PAA, GSC, Google Search Console, DataForSEO, or DFS as source attribution in
  customer-facing copy.
- State supported details directly and naturally without explaining where they
  came from.
- Internal-source terms are allowed when they are genuinely part of the topic,
  target keyword, service, product, or official name. The word "page" is also
  allowed in those cases, but never use either as source attribution.
- Internal structured fields required by the output schema may retain their
  required JSON metadata values; do not expose those values in customer-facing
  text.
""".strip()


_NON_US_ENGLISH_SPELLING = re.compile(
    r"\b(?:"
    r"analys(?:e|ed|es|ing|er|ers)"
    r"|authoris(?:e|ed|es|ing|ation|ations)"
    r"|behaviours?|behavioural"
    r"|cancelled|cancelling"
    r"|catalogues?|catalogued|cataloguing"
    r"|centres?|centred|centring"
    r"|colours?|coloured|colouring"
    r"|customis(?:e|ed|es|ing|ation|ations)"
    r"|defences?|offences?"
    r"|emphasis(?:e|ed|es|ing)"
    r"|favours?|favoured|favouring|favourites?"
    r"|fulfils?|fulfilment"
    r"|honours?|honoured|honouring"
    r"|labelled|labelling"
    r"|labours?|laboured|labouring"
    r"|licences?"
    r"|maximis(?:e|ed|es|ing|ation)"
    r"|minimis(?:e|ed|es|ing|ation)"
    r"|modelled|modelling"
    r"|neighbours?|neighbourhoods?"
    r"|organis(?:e|ed|es|ing|er|ers|ation|ations|ational)"
    r"|optimis(?:e|ed|es|ing|ation|ations)"
    r"|personalis(?:e|ed|es|ing|ation)"
    r"|prioritis(?:e|ed|es|ing|ation)"
    r"|programmes?"
    r"|recognis(?:e|ed|es|ing|able|ably|ation)"
    r"|specialis(?:e|ed|es|ing|ation|ations)"
    r"|summaris(?:e|ed|es|ing|ation)"
    r"|travelled|travelling"
    r"|whilst|amongst|learnt|spelt"
    r")\b",
    re.IGNORECASE,
)


def find_non_us_english_spellings(
    text: str,
    protected_phrases: Iterable[str] = (),
) -> list[str]:
    """Return distinct high-confidence non-U.S. spellings outside protected text."""
    candidate = str(text or "")
    phrases = {
        str(phrase).strip()
        for phrase in protected_phrases
        if str(phrase or "").strip()
    }
    for phrase in sorted(phrases, key=len, reverse=True):
        candidate = re.sub(re.escape(phrase), " ", candidate, flags=re.IGNORECASE)

    matches = []
    seen = set()
    for match in _NON_US_ENGLISH_SPELLING.finditer(candidate):
        value = match.group(0)
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            matches.append(value)
    return matches
