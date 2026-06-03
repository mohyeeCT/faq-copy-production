# Niche registry — injected into every AI prompt alongside business_type.
# Each niche provides: buyer persona, primary concerns, trusted terminology,
# trust signals, CTA patterns, tone guidance, and compliance notes where relevant.

NICHES: dict[str, dict] = {
    "none": {
        "label": "No specific niche",
        "group": "General",
        "business_types": ["b2b", "b2c", "ecommerce", "service", "local", "general"],
        "context": "",
    },

    # ── B2B ───────────────────────────────────────────────────────────────────

    "manufacturing_industrial": {
        "label": "Manufacturing / Industrial",
        "group": "B2B",
        "business_types": ["b2b", "general"],
        "context": (
            "NICHE: Manufacturing and industrial B2B.\n"
            "Buyer persona: Engineers, procurement managers, operations directors, plant managers. "
            "Long buying cycles (3-12 months), committee decisions, multiple technical stakeholders.\n"
            "Primary concerns: Reliability and uptime, regulatory compliance and certifications (ISO, CE, ATEX), "
            "total cost of ownership, lead times, supply chain reliability, technical tolerances.\n"
            "Terminology that resonates: throughput, yield, OEE, downtime reduction, ROI, compliance, "
            "traceability, tolerances, capacity, batch consistency, audit trail.\n"
            "Trust signals: ISO certifications, industry accreditations, case studies with named clients "
            "and measurable outcomes (e.g. reduced downtime by X%), technical datasheets, long client tenures.\n"
            "CTA patterns: Request a technical consultation, download datasheet, get a quote, speak to an engineer.\n"
            "Tone: Technical, credible, data-led. No consumer language. No hyperbole. "
            "Claims must be specific and provable."
        ),
    },

    "saas_software": {
        "label": "SaaS / Software",
        "group": "B2B",
        "business_types": ["b2b", "general"],
        "context": (
            "NICHE: B2B SaaS or software product.\n"
            "Buyer persona: CTO, VP Engineering, Product Manager, IT Director, or team lead evaluating tools. "
            "Buying cycle 1-6 months, often freemium or trial-led, multiple stakeholder sign-off above a threshold.\n"
            "Primary concerns: Integration with existing tech stack, security and compliance (SOC2, GDPR, ISO27001), "
            "scalability, time to value, onboarding quality, pricing model clarity, vendor lock-in risk.\n"
            "Terminology that resonates: API, native integrations, workflow automation, time-to-value, ROI, "
            "uptime SLA, data security, scalability, onboarding, churn reduction, seat-based pricing.\n"
            "Trust signals: G2/Capterra ratings (with specific score), named enterprise customers, "
            "security certifications, case studies with measurable outcomes (hours saved, revenue impact), "
            "free trial or interactive demo.\n"
            "CTA patterns: Start free trial, book a demo, see it in action, get started free.\n"
            "Tone: Clear, confident, outcome-focused. Lead with the problem solved, not the feature list. "
            "The reader evaluates 3-5 tools simultaneously — differentiate on outcome and integration, not UI."
        ),
    },

    "financial_services": {
        "label": "Financial Services / Fintech",
        "group": "B2B",
        "business_types": ["b2b", "general"],
        "context": (
            "NICHE: B2B financial services, fintech, accounting software, or financial advisory.\n"
            "Buyer persona: CFO, Finance Director, Controller, Treasurer, compliance officer. "
            "Extremely risk-averse. Buying cycle 3-18 months. Requires board or committee sign-off.\n"
            "Primary concerns: Regulatory compliance (FCA, SEC, GDPR, SOX, PSD2), data security and sovereignty, "
            "accuracy and auditability, integration with ERP/accounting systems, TCO, vendor financial stability.\n"
            "Terminology that resonates: compliance, regulatory approval, audit trail, reconciliation, "
            "risk management, fiduciary duty, real-time reporting, cost reduction, accuracy, data sovereignty.\n"
            "Trust signals: Regulatory approvals and licences, named financial institution clients, "
            "FCA authorisation, security certifications, years of financial services specialisation.\n"
            "CTA patterns: Book a consultation, request a regulated demo, speak to a specialist.\n"
            "COMPLIANCE NOTE: Avoid unqualified financial performance claims. Do not promise specific returns. "
            "Use appropriately hedged language for any outcome claims. Check FCA financial promotion rules.\n"
            "Tone: Precise, conservative, trust-building. Credibility over persuasion. "
            "Every claim must be substantiable."
        ),
    },

    "it_msp": {
        "label": "IT / MSP",
        "group": "B2B",
        "business_types": ["b2b", "service", "general"],
        "context": (
            "NICHE: IT services, managed service providers, cybersecurity, cloud services, or IT support.\n"
            "Buyer persona: IT Director, CTO, Operations Manager, or SME owner without dedicated IT team. "
            "Buying trigger: security incident, growth, staff frustration with current provider, or compliance requirement.\n"
            "Primary concerns: Security and data protection, SLA and uptime guarantees, response times, "
            "compliance (GDPR, ISO27001, Cyber Essentials), scalability, predictable monthly cost.\n"
            "Terminology that resonates: SLA, uptime guarantee, mean time to respond, patch management, "
            "endpoint security, backup and disaster recovery, proactive monitoring, helpdesk.\n"
            "Trust signals: Cyber Essentials Plus, ISO27001, Microsoft/Google partner status, "
            "SLA commitments with specific response times, named SME or enterprise clients, years in business.\n"
            "CTA patterns: Get a free IT audit, book a consultation, speak to an engineer, get a quote.\n"
            "Tone: Reliable, no-nonsense, specific. Name SLA numbers, response times, and certifications. "
            "Avoid vague reassurances — the buyer has heard them from the incumbent and does not trust them."
        ),
    },

    "professional_services": {
        "label": "Professional Services / Consulting",
        "group": "B2B",
        "business_types": ["b2b", "service", "general"],
        "context": (
            "NICHE: Management consulting, business consulting, HR consulting, operations, or strategy advisory.\n"
            "Buyer persona: CEO, Director, or senior manager buying external expertise for a specific challenge. "
            "Buying cycle 1-3 months, highly relationship-driven, often referral-sourced.\n"
            "Primary concerns: Relevant industry experience, proven methodology, measurable outcomes, "
            "cultural fit, confidentiality, value for fee, who specifically will work on their account.\n"
            "Terminology that resonates: transformation, capability building, strategic alignment, "
            "change management, ROI, measurable outcomes, proprietary framework, methodology, accountability.\n"
            "Trust signals: Named client case studies (or anonymised sector + outcome), team credentials, "
            "thought leadership, testimonials from senior decision-makers, tenure of client relationships.\n"
            "CTA patterns: Book a discovery call, request a proposal, speak with a consultant.\n"
            "Tone: Peer-to-peer — authoritative without arrogance. Demonstrate strategic thinking quality "
            "through the copy itself. Do not list credentials before demonstrating understanding of the problem."
        ),
    },

    "hr_recruitment": {
        "label": "HR / Recruitment",
        "group": "B2B",
        "business_types": ["b2b", "service", "general"],
        "context": (
            "NICHE: Recruitment agency, HR software, talent acquisition, or HR consulting.\n"
            "Buyer persona: HR Director, Talent Acquisition Manager, or CEO of an SME with hiring needs. "
            "Buying trigger: volume hiring, senior role, bad previous agency experience, or compliance gap.\n"
            "Primary concerns: Speed to hire, candidate quality and retention, compliance (GDPR, IR35, "
            "employment law), cost per hire, sector specialisation, post-placement support.\n"
            "Terminology that resonates: time-to-hire, first-year retention, passive candidates, "
            "talent pipeline, employer brand, IR35 compliance, headcount planning, dedicated consultant.\n"
            "Trust signals: Placement success rate, named employer clients, sector specialisation, "
            "retention metrics, testimonials from both employers and placed candidates.\n"
            "CTA patterns: Submit a vacancy, book a call, discuss your hiring needs.\n"
            "Tone: Human and direct. Show understanding of both sides — employer urgency and candidate experience."
        ),
    },

    "logistics_supply_chain": {
        "label": "Logistics / Supply Chain",
        "group": "B2B",
        "business_types": ["b2b", "general"],
        "context": (
            "NICHE: Freight, logistics, warehousing, 3PL, or supply chain services.\n"
            "Buyer persona: Supply Chain Manager, Logistics Director, Operations Manager, or Procurement Lead. "
            "Buying cycle 1-6 months. Multi-site or multi-country operations common.\n"
            "Primary concerns: Reliability and on-time delivery rates, track and trace capability, "
            "cost per shipment, scalability for peak seasons, customs and compliance for cross-border, "
            "integration with WMS/ERP systems.\n"
            "Terminology that resonates: on-time delivery rate, track and trace, SLA, last-mile, "
            "customs clearance, bonded warehouse, 3PL, API integration, peak capacity.\n"
            "Trust signals: Named shipper clients, delivery performance data, network coverage map, "
            "ISO 9001 or equivalent, years of operation, sector specialisation.\n"
            "CTA patterns: Request a quote, discuss your logistics needs, get a network overview.\n"
            "Tone: Operational, specific, and data-led. Buyers do not want aspirational language — "
            "they want network coverage, delivery rates, and SLA guarantees."
        ),
    },

    # ── Service / Local ────────────────────────────────────────────────────────

    "law_firm": {
        "label": "Law Firm / Legal Services",
        "group": "Service / Local",
        "business_types": ["service", "local", "b2b", "general"],
        "context": (
            "NICHE: Legal services — consumer or B2B law firm.\n"
            "Buyer persona: Individual or business facing a legal issue, often stressed and seeking clarity. "
            "Buying trigger: urgent legal need, contract dispute, employment issue, personal injury, or property transaction.\n"
            "Primary concerns: Expertise in this specific area of law, outcome track record, fee transparency, "
            "communication quality and responsiveness, how long it will take.\n"
            "Terminology that resonates: specialist, qualified solicitor, free initial consultation, "
            "transparent fees, plain English advice, no-win-no-fee (where applicable), experience in this area.\n"
            "Trust signals: Legal 500 / Chambers rankings, SRA accreditation, practice area specialisation, "
            "Google and independent review ratings, years handling this type of case specifically.\n"
            "CTA patterns: Book a free consultation, call now, get expert legal advice today.\n"
            "COMPLIANCE NOTE: Do not guarantee outcomes. Do not use outcome success rates without full "
            "substantiation. Follow SRA advertising standards — no misleading claims. "
            "Regulated financial promotions rules apply for certain practice areas.\n"
            "Tone: Confident, clear, and reassuring. Plain English throughout. "
            "The reader is anxious — the copy must feel authoritative and human, not legalistic."
        ),
    },

    "dental_medical": {
        "label": "Dental / Medical Practice",
        "group": "Service / Local",
        "business_types": ["service", "local", "general"],
        "context": (
            "NICHE: Dental practice, GP surgery, specialist clinic, or private medical provider.\n"
            "Buyer persona: Patient seeking treatment, often anxious or in discomfort. "
            "May be comparing NHS vs private options. Trust and comfort are the primary purchase drivers.\n"
            "Primary concerns: Clinical expertise, pain management and comfort, cost and payment options, "
            "waiting times, hygiene standards, location and accessibility, staff manner.\n"
            "Terminology that resonates: experienced team, gentle approach, nervous patients welcome, "
            "modern equipment, flexible payment plans, convenient appointments, CQC registered.\n"
            "Trust signals: GDC/GMC registration, named clinician credentials, "
            "Google reviews specifically mentioning anxiety management or clinical quality, "
            "awards or accreditations, years in practice, patient before/after (with ethical consent).\n"
            "CTA patterns: Book an appointment, request a callback, call today.\n"
            "COMPLIANCE NOTE: Avoid unsubstantiated before/after claims. Do not make medical claims "
            "for cosmetic procedures. Follow ASA/CAP and GDC advertising guidance. "
            "CQC regulation compliance language required for regulated activities.\n"
            "Tone: Warm, reassuring, and clear. The reader is often anxious. "
            "Avoid clinical jargon in patient-facing copy. Make the first step feel easy."
        ),
    },

    "hvac_trades": {
        "label": "HVAC / Plumbing / Trades",
        "group": "Service / Local",
        "business_types": ["service", "local", "general"],
        "context": (
            "NICHE: HVAC, plumbing, electrical, roofing, or general trades contractor.\n"
            "Buyer persona: Homeowner or property manager with an urgent or planned maintenance need. "
            "Often comparing 2-3 quotes. May have had a bad experience with a previous contractor.\n"
            "Primary concerns: Reliability (showing up on time), trade qualifications and insurance, "
            "transparent pricing, workmanship guarantee, local reputation.\n"
            "Terminology that resonates: Gas Safe registered, NICEIC approved, fully insured, "
            "free no-obligation quote, same-day availability, emergency callout, satisfaction guarantee.\n"
            "Trust signals: Trade certifications (Gas Safe, NICEIC, NAPIT, ELECSA), "
            "public liability insurance, Which? Trusted Trader, Google reviews mentioning reliability, "
            "years serving the local area, named suburbs and towns served.\n"
            "CTA patterns: Call now for a free quote, book online, emergency? Call 24/7.\n"
            "Tone: Straight-talking, reliable, local. No corporate language. "
            "Readers want to know you are trustworthy and you will show up when you say you will. "
            "Be specific about what is included in the service."
        ),
    },

    "real_estate": {
        "label": "Real Estate / Property",
        "group": "Service / Local",
        "business_types": ["service", "local", "b2b", "general"],
        "context": (
            "NICHE: Estate agency, property management, conveyancing, or real estate investment.\n"
            "Buyer persona: Buyer, seller, landlord, or tenant. High-stakes transaction. "
            "Often anxious, comparing multiple agents, and motivated by trust in local expertise.\n"
            "Primary concerns: Local market knowledge, track record of sales and lettings achieved, "
            "fees and commission transparency, communication and responsiveness, time to sell or let.\n"
            "Terminology that resonates: local expertise, average sale time, percentage of asking price achieved, "
            "managed portfolio, rigorous tenant vetting, no hidden fees, accompanied viewings.\n"
            "Trust signals: Number of sales/lettings, average days on market vs local average, "
            "percentage of asking price achieved, local office presence, Google reviews with local context, "
            "named area testimonials.\n"
            "CTA patterns: Get a free valuation, list your property, speak to a local expert.\n"
            "Tone: Confident, locally knowledgeable. Name streets, areas, and local context. "
            "Sellers and landlords want an agent who knows the area, not a national franchise script."
        ),
    },

    "accountancy_tax": {
        "label": "Accountancy / Tax",
        "group": "Service / Local",
        "business_types": ["service", "local", "b2b", "general"],
        "context": (
            "NICHE: Accountancy firm, tax advisor, bookkeeping service, or financial planning.\n"
            "Buyer persona: SME owner, director, or individual needing tax or accounting help. "
            "Motivated by compliance, cost savings, and peace of mind. "
            "Often switching from a passive accountant who only does year-end.\n"
            "Primary concerns: Accuracy and HMRC compliance, proactive year-round advice, "
            "fees and value clarity, ease of switching, specialisation in their sector or situation.\n"
            "Terminology that resonates: tax savings, HMRC compliant, proactive advice, "
            "cloud accounting, Xero/QuickBooks, quarterly reviews, tax-efficient structure, fixed monthly fee.\n"
            "Trust signals: ICAEW/ACCA/CIMA membership, Xero/QuickBooks platinum certification, "
            "sector specialisation, named client types, specific tax savings examples, Google reviews.\n"
            "CTA patterns: Book a free consultation, get a fixed fee quote, switch accountant today.\n"
            "Tone: Approachable, expert, and proactively helpful. "
            "Position this firm as the accountant who calls you before tax season, not after. "
            "Most clients are switching because their current accountant does the minimum."
        ),
    },

    "fitness_wellness": {
        "label": "Fitness / Wellness",
        "group": "Service / Local",
        "business_types": ["service", "local", "b2c", "general"],
        "context": (
            "NICHE: Gym, personal trainer, physiotherapist, nutritionist, or wellness coach.\n"
            "Buyer persona: Individual with a health goal (weight loss, strength, rehab, or performance). "
            "Often has tried and failed before. Needs proof it will work for someone like them specifically.\n"
            "Primary concerns: Real results from real people, value for money, "
            "location and schedule convenience, community and accountability, approach and personality fit.\n"
            "Terminology that resonates: transformation, results, accountability, bespoke programme, "
            "free trial session, flexible membership, no long-term contract, progress tracking.\n"
            "Trust signals: Client transformation stories with permission, qualifications (Level 3/4 PT, REPs), "
            "before/after results where appropriate, Google reviews mentioning specific outcomes.\n"
            "CTA patterns: Book a free consultation, claim your first session free, start your trial.\n"
            "COMPLIANCE NOTE: Do not make guaranteed weight loss or health claims. "
            "Follow ASA guidelines for fitness advertising. "
            "Before/after images require appropriate context and consent.\n"
            "Tone: Motivating, honest, and human. The reader wants to believe change is possible for them "
            "specifically — address previous setbacks with empathy before presenting the solution."
        ),
    },

    "childcare_education": {
        "label": "Childcare / Education",
        "group": "Service / Local",
        "business_types": ["service", "local", "general"],
        "context": (
            "NICHE: Nursery, childcare, tutoring, private school, or educational service.\n"
            "Buyer persona: Parent or guardian evaluating providers for their child. "
            "High-stakes decision. Emotional and rational — safety and Ofsted rating first, "
            "outcomes and fees second.\n"
            "Primary concerns: Safety and safeguarding credentials, Ofsted rating, "
            "staff qualifications and ratios, curriculum and educational approach, location and hours, fees.\n"
            "Terminology that resonates: Outstanding Ofsted, qualified staff, key worker, "
            "EYFS framework, wraparound care, funded hours, nurturing environment, "
            "low child-to-staff ratio, individual learning plans.\n"
            "Trust signals: Ofsted Outstanding or Good rating (with date), "
            "named staff qualifications, years in operation, parent testimonials (with child's first name), "
            "DBS checked staff, safeguarding policy.\n"
            "CTA patterns: Book a visit, arrange a trial session, apply for a place.\n"
            "Tone: Warm, reassuring, and professionally confident. "
            "Parents are making one of the most important decisions for their child — "
            "the copy must feel safe, trustworthy, and human. Name the team, not just the setting."
        ),
    },

    "marketing_agency": {
        "label": "Marketing Agency / Creative",
        "group": "Service / Local",
        "business_types": ["service", "b2b", "general"],
        "context": (
            "NICHE: Digital marketing, SEO, creative, or PR agency.\n"
            "Buyer persona: Marketing Director, CMO, or business owner evaluating agency partners. "
            "Sophisticated and sceptical — they know the buzzwords and have been burned by overpromising agencies.\n"
            "Primary concerns: Proven results in their specific industry, reporting transparency, "
            "communication quality and frequency, who actually works on the account (not bait-and-switch), "
            "value for retainer, compatibility with existing team.\n"
            "Terminology that resonates: ROI, attribution, organic growth, data-driven decisions, "
            "transparent reporting, dedicated account manager, measurable results, no lock-in contracts.\n"
            "Trust signals: Named case studies with real metrics (not anonymised), "
            "named senior team members, Google/Meta/HubSpot partner badges, industry awards, "
            "client tenure (average relationship length is a strong signal).\n"
            "CTA patterns: Book a strategy call, request a proposal, get a free audit.\n"
            "Tone: Peer-to-peer — strategic partner, not a vendor. "
            "Demonstrate thinking quality through the copy itself. "
            "Avoid agency clichés: 'full-service', 'digital-first', 'growth hackers', 'synergies'. "
            "Every claim needs a number behind it."
        ),
    },

    # ── Ecommerce ──────────────────────────────────────────────────────────────

    "fashion_apparel": {
        "label": "Fashion / Apparel",
        "group": "Ecommerce",
        "business_types": ["ecommerce", "b2c", "general"],
        "context": (
            "NICHE: Fashion, clothing, footwear, or accessories ecommerce.\n"
            "Buyer persona: Consumer shopping for style, identity expression, or a specific occasion. "
            "Purchase driven by visual appeal, fit confidence, trend relevance, and brand identity.\n"
            "Primary concerns: Fit and sizing accuracy (reduce returns), fabric quality and care, "
            "brand identity alignment, delivery speed and cost, returns policy ease.\n"
            "Terminology that resonates: true to size, flattering cut, versatile, limited edition, "
            "ethically made, free returns within 30 days, next-day delivery, new arrivals, sizes X-X.\n"
            "Trust signals: Customer UGC and styled photos, accurate size guides, "
            "star ratings with volume, sustainability credentials (where genuine), "
            "named materials (100% organic cotton, GOTS certified).\n"
            "CTA patterns: Shop now, find your fit, explore the collection, shop the look.\n"
            "Tone: Brand-led, aspirational but accessible. "
            "Fashion copy is shorter and more evocative than utility copy — "
            "every word should carry the brand's identity. Match the visual aesthetic in tone."
        ),
    },

    "beauty_skincare": {
        "label": "Beauty / Skincare",
        "group": "Ecommerce",
        "business_types": ["ecommerce", "b2c", "general"],
        "context": (
            "NICHE: Beauty, skincare, cosmetics, or personal care ecommerce.\n"
            "Buyer persona: Consumer seeking a solution to a specific skin concern or adding to a routine. "
            "Research-heavy — compares ingredients, reads INCI lists, checks Reddit and Trustpilot before buying.\n"
            "Primary concerns: Ingredient transparency, skin type suitability, clinical or dermatologist backing, "
            "ethical credentials (cruelty-free, vegan), realistic results timeline.\n"
            "Terminology that resonates: dermatologist-tested, clinically proven, cruelty-free, vegan, "
            "clean beauty, hyaluronic acid, retinol, niacinamide, SPF, fragrance-free, "
            "suitable for sensitive/oily/dry/combination skin.\n"
            "Trust signals: Before/after results with ethical consent and appropriate disclaimers, "
            "dermatologist endorsement, full ingredient transparency, Leaping Bunny or PETA certification, "
            "verified reviews mentioning specific skin types and concerns.\n"
            "CTA patterns: Shop the range, find your routine, try it today, add to routine.\n"
            "COMPLIANCE NOTE: Do not make medical claims for cosmetic products. "
            "'Treats acne' is a medical claim — use 'helps reduce the appearance of blemishes' instead. "
            "SPF claims require regulatory compliance. Follow ASA/CAP beauty advertising rules.\n"
            "Tone: Expert and accessible. Show why the formulation works, not just what it claims to do."
        ),
    },

    "home_garden": {
        "label": "Home & Garden",
        "group": "Ecommerce",
        "business_types": ["ecommerce", "b2c", "general"],
        "context": (
            "NICHE: Home furnishings, garden, DIY, or home improvement ecommerce.\n"
            "Buyer persona: Homeowner or renter personalising their living space or tackling a project. "
            "Purchase often planned and comparison-heavy. Visualisation is the primary purchase barrier.\n"
            "Primary concerns: Exact dimensions and fit, durability and materials quality, "
            "style compatibility with existing decor, delivery and assembly complexity, returns for large items.\n"
            "Terminology that resonates: easy self-assembly, solid wood/real stone/genuine leather, "
            "weatherproof, compatible with standard UK sizing, free delivery over X, "
            "easy returns, 2-year guarantee, available in X colours.\n"
            "Trust signals: Precise dimensions in cm and inches, customer photos in real homes, "
            "material composition, delivery timeline transparency, clear return policy, Trustpilot reviews.\n"
            "CTA patterns: Shop the collection, view all sizes, get inspired, see in a room.\n"
            "Tone: Practical and inspiring in equal measure. "
            "Give the reader the technical confidence to buy (dimensions, materials, assembly) "
            "then connect it to how their home will feel."
        ),
    },

    "sports_outdoors": {
        "label": "Sports / Outdoors",
        "group": "Ecommerce",
        "business_types": ["ecommerce", "b2c", "general"],
        "context": (
            "NICHE: Sports equipment, outdoor gear, activewear, or fitness product ecommerce.\n"
            "Buyer persona: Active consumer researching performance gear. "
            "Often an enthusiast with above-average product knowledge. "
            "Motivated by performance, durability, and brand credibility within their specific sport.\n"
            "Primary concerns: Technical specifications (waterproof rating, weight, material technology), "
            "durability and longevity, brand credibility within the sport, fit and comfort, value per use.\n"
            "Terminology that resonates: waterproof rating (20,000mm HH), breathable membrane, "
            "lightweight (specific gram weight), trail-tested, 2-year warranty, "
            "compatible with [system], technical seams, recycled materials.\n"
            "Trust signals: Specific technical specs (not vague 'waterproof' — give the rating), "
            "athlete or expert endorsements, field-tested credentials, "
            "verified buyer reviews mentioning specific use conditions.\n"
            "CTA patterns: Shop the range, compare models, find your size, gear up.\n"
            "Tone: Performance-led and credible. The reader knows their sport — match their vocabulary. "
            "Be specific about activity and conditions. Avoid generic outdoor marketing language."
        ),
    },

    "food_beverage": {
        "label": "Food & Beverage",
        "group": "Ecommerce",
        "business_types": ["ecommerce", "b2c", "general"],
        "context": (
            "NICHE: Food, drink, or subscription food box ecommerce.\n"
            "Buyer persona: Consumer motivated by taste, health credentials, convenience, or ethical sourcing. "
            "Subscription products must overcome inertia and habit — the reader is comparing to their current routine.\n"
            "Primary concerns: Taste and quality, ingredient transparency and allergens, "
            "delivery freshness, ethical and sustainability credentials, value vs supermarket alternatives.\n"
            "Terminology that resonates: freshly sourced, artisan, organic, "
            "full allergen information, subscription flexibility, cancel anytime, "
            "farm-to-door, free from [ingredient], Soil Association certified.\n"
            "Trust signals: Sourcing story and producer names, customer reviews mentioning taste specifically, "
            "food safety certifications, Great Taste Award or equivalent press coverage.\n"
            "CTA patterns: Try your first box, order now, subscribe and save, try risk-free.\n"
            "COMPLIANCE NOTE: Health claims must be authorised under UK/EU food law. "
            "Do not make unqualified health benefit claims. Nutritional data must be accurate.\n"
            "Tone: Sensory and warm. Good food copy makes the reader almost taste or smell the product. "
            "Be specific about flavour, texture, and provenance — not generic freshness claims."
        ),
    },

    "electronics_tech": {
        "label": "Electronics / Consumer Tech",
        "group": "Ecommerce",
        "business_types": ["ecommerce", "b2c", "general"],
        "context": (
            "NICHE: Consumer electronics, gadgets, or tech accessories ecommerce.\n"
            "Buyer persona: Tech-savvy consumer or gift buyer comparing specifications across 3-5 products. "
            "Research-heavy, reviews-driven, and specification-led. "
            "Decision is often made on one or two critical specs.\n"
            "Primary concerns: Exact technical specifications (battery life in hours, resolution, "
            "Bluetooth version, compatibility), reliability and build quality, "
            "warranty terms and customer support, price vs. alternatives.\n"
            "Terminology that resonates: battery life (specific hours), resolution (exact), "
            "Bluetooth 5.3, compatible with iOS and Android, 2-year warranty, fast charging (specific watt), "
            "IP68 water resistance, refresh rate, latency.\n"
            "Trust signals: Precise technical specifications (not vague claims), "
            "compatibility matrix, warranty terms clearly stated, "
            "verified customer reviews mentioning real-world battery life or performance.\n"
            "CTA patterns: Buy now, check compatibility, compare models, see full specs.\n"
            "Tone: Precise and specification-led. The reader wants facts, not hype. "
            "Lead with the spec that matters most for this product type. "
            "Keep emotional language for the closing — earn it with specs first."
        ),
    },

    "supplements_nutrition": {
        "label": "Supplements / Nutrition",
        "group": "Ecommerce",
        "business_types": ["ecommerce", "b2c", "general"],
        "context": (
            "NICHE: Sports supplements, vitamins, health nutrition, or wellness products ecommerce.\n"
            "Buyer persona: Health-conscious consumer or athlete seeking a specific outcome — "
            "performance, recovery, weight management, or general health support. "
            "Sophisticated buyer — checks ingredients and third-party testing before purchasing.\n"
            "Primary concerns: Ingredient transparency and clinical dosing, third-party testing, "
            "evidence behind the formulation, taste and mixability (for powders), value per serving, "
            "absence of banned substances.\n"
            "Terminology that resonates: third-party tested, clinically dosed, no proprietary blends, "
            "Informed Sport or NSF certified, cost per serving, GMP-certified facility, unflavoured option, "
            "vegan capsules, third-party lab reports available.\n"
            "Trust signals: Informed Sport certification, full label transparency (no proprietary blends), "
            "third-party testing documentation, athlete reviews with specific outcomes, "
            "money-back guarantee, years in formulation.\n"
            "CTA patterns: Shop now, find your stack, try risk-free, subscribe and save.\n"
            "COMPLIANCE NOTE: MHRA and ASA rules apply strictly. Do not make disease treatment or "
            "prevention claims. Do not make specific performance claims without full substantiation. "
            "Only use authorised EU/UK health claims for vitamins and minerals. "
            "No claims implying pharmaceutical effect.\n"
            "Tone: Expert and evidence-led. Show ingredient quality before making any outcome claims. "
            "The target buyer is knowledgeable — condescending or oversimplified copy will lose them."
        ),
    },
}


def get_niche_context(niche_key: str) -> str:
    """Return the context string for a given niche key. Empty string if not found or 'none'."""
    niche = NICHES.get(niche_key or "none", {})
    return niche.get("context", "")


def get_niche_options() -> list[dict]:
    """Return all niches as a list of dicts for API responses."""
    return [
        {
            "key": k,
            "label": v["label"],
            "group": v["group"],
            "business_types": v["business_types"],
        }
        for k, v in NICHES.items()
    ]
