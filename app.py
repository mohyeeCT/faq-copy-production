import streamlit as st
import pandas as pd
import json
import re
import time
from io import StringIO

from utils.sheets import get_gspread_client, load_sheet, write_results_to_sheet
from utils.gsc import get_gsc_client, get_top_queries_for_url
from utils.dfs import get_keyword_overview, get_keyword_difficulty, get_people_also_ask
from utils.keyword import select_keyword
from utils.copy_gen import generate_faq, build_faq_schema
from utils.scraper import scrape_page_context


# ── Helpers ───────────────────────────────────────────────────────────────────

def _empty_result(
    url: str,
    status: str,
    num_faqs: int,
    keyword: str = None,
    source: str = None,
    scrape_status: str = "skipped"
) -> dict:
    r = {
        "url": url,
        "selected_keyword": keyword,
        "keyword_source": source,
        "runner_up": None,
        "kw_volume": None,
        "kw_difficulty": None,
        "scrape_status": scrape_status,
        "paa_count": 0,
        "faq_count": 0,
        "faq_schema_jsonld": "",
        "status": status,
    }
    for idx in range(1, num_faqs + 1):
        r[f"faq_{idx}_question"] = ""
        r[f"faq_{idx}_answer"] = ""
    return r


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="FAQ Copy Production",
    page_icon="",
    layout="wide"
)

st.title("FAQ Copy Production")
st.caption("Generate FAQ sections from People Also Ask data using GSC + DataForSEO + AI.")

# ── Sidebar: credentials ──────────────────────────────────────────────────────

with st.sidebar:
    st.header("Credentials")
    sa_file = st.file_uploader(
        "Service Account JSON", type=["json"],
        help="Same service account used for Google Sheets and GSC access."
    )

    st.divider()
    st.subheader("DataForSEO")
    dfs_login = st.text_input("Login (email)", type="default")
    dfs_password = st.text_input("Password", type="password")

    st.divider()
    st.subheader("FireCrawl")
    firecrawl_key = st.text_input(
        "FireCrawl API Key", type="password",
        help="Used to scrape page content for topic context. Get yours at firecrawl.dev."
    )
    enable_scraping = st.toggle(
        "Enable page scraping",
        value=True,
        help="Scrapes ~50% of each page to ground FAQs in actual page content. Disable to skip scraping and rely on keyword + PAA only."
    )

    st.divider()
    st.subheader("AI Provider")
    ai_provider = st.selectbox("Provider", [
        "Claude",
        "OpenAI",
        "Gemini (free)",
        "Mistral (free tier)",
        "Groq (free tier)"
    ])

    _key_labels = {
        "Claude": ("Claude API Key", "console.anthropic.com"),
        "OpenAI": ("OpenAI API Key", "platform.openai.com/api-keys"),
        "Gemini (free)": ("Google AI Studio API Key", "aistudio.google.com/app/apikey"),
        "Mistral (free tier)": ("Mistral API Key", "console.mistral.ai"),
        "Groq (free tier)": ("Groq API Key", "console.groq.com"),
    }
    _label, _hint = _key_labels[ai_provider]
    ai_key = st.text_input(_label, type="password", help=_hint)

    st.divider()
    st.subheader("Copy Settings")

    business_type = st.selectbox(
        "Business Type",
        ["b2b", "b2c", "ecommerce", "service", "local", "general"],
        help="Adjusts tone, CTA style, and copy patterns."
    )

    brand_name = st.text_input("Brand Name", placeholder="Acme Inc.")

    full_brand_name = st.text_input(
        "Full Brand Name (optional)",
        placeholder="Dayson Shalabi Burkert",
        help="If the brand is an abbreviation (e.g. DSB), enter the full name. Each word is added to the branded filter."
    )

    num_faqs = st.slider(
        "Number of FAQs per page",
        min_value=3, max_value=10, value=5,
        help="How many Q&A pairs to generate per URL."
    )

    forbidden_phrases = st.text_area(
        "Forbidden Phrases (one per line)",
        placeholder="best in class\nworld-class\namazing",
        height=80
    )

    branded_terms_input = st.text_area(
        "Branded Terms to Exclude (one per line)",
        placeholder="acme\nacme inc",
        height=60
    )

    location_code = st.number_input(
        "DFS Location Code", value=2840, step=1,
        help="2840 = US. See DataForSEO docs for other locations."
    )

    min_volume = st.number_input(
        "Min Keyword Volume", value=10, step=10,
        help="Lower for niche B2B sites. Set to 0 to disable."
    )

# ── Section 1: Connect to Google Sheet ───────────────────────────────────────

st.header("1. Connect to Google Sheet")

col1, col2 = st.columns([3, 1])
with col1:
    sheet_url = st.text_input(
        "Google Sheet URL",
        placeholder="https://docs.google.com/spreadsheets/d/..."
    )
with col2:
    worksheet_name = st.text_input("Worksheet Name", placeholder="Leave blank for first sheet")

st.caption("Sheet must have at minimum: a URL column. Optional: keyword, page type, H1.")

if sheet_url and sa_file:
    try:
        sa_info = json.load(sa_file)
        sa_email = sa_info.get("client_email", "unknown")
        st.info(f"Service account: **{sa_email}** - make sure this email has Editor access to the sheet.")
        gc = get_gspread_client(sa_info)
        df, spreadsheet, ws = load_sheet(gc, sheet_url, worksheet_name or None)
        st.success(f"Connected. {len(df)} rows loaded.")
        st.dataframe(df.head(5), use_container_width=True)
        st.session_state["df"] = df
        st.session_state["ws"] = ws
        st.session_state["sa_info"] = sa_info
    except Exception as e:
        st.error(f"Could not connect to sheet: {e}")
        st.caption(
            "Common causes: (1) sheet not shared with the service account, "
            "(2) wrong sheet URL, (3) Sheets API not enabled in Cloud Console."
        )

# ── Section 2: Column mapping ─────────────────────────────────────────────────

if "df" in st.session_state:
    st.header("2. Map Columns")
    df = st.session_state["df"]
    cols = ["(none)"] + list(df.columns)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        url_col = st.selectbox("URL column *", [c for c in cols if c != "(none)"] or cols)
    with col2:
        keyword_col = st.selectbox("Keyword column (optional)", cols)
    with col3:
        page_type_col = st.selectbox("Page type column (optional)", cols)
    with col4:
        h1_col = st.selectbox(
            "H1 column (optional)", cols,
            help="Current page H1 used as context for FAQ generation."
        )

    st.divider()

    # ── Section 3: GSC Settings ───────────────────────────────────────────────

    st.header("3. GSC Settings")
    gsc_site_url = st.text_input(
        "GSC Property URL",
        placeholder="https://example.com/ or sc-domain:example.com"
    )

    # ── Section 4: Brand Detection ────────────────────────────────────────────

    st.header("4. Brand Detection")

    detect_ready = (
        sa_file is not None and
        gsc_site_url and
        "df" in st.session_state and
        "sa_info" in st.session_state
    )

    if detect_ready:
        detect_btn = st.button("Auto-detect Branded Terms", type="secondary")
        if detect_btn:
            with st.spinner("Scanning GSC queries for branded signals..."):
                _sa_info = st.session_state["sa_info"]
                _gsc = get_gsc_client(_sa_info)
                _df = st.session_state["df"].copy()
                _sample_urls = _df[url_col].dropna().tolist()[:10]

                _all_queries = {}
                for _url in _sample_urls:
                    _url = str(_url).strip()
                    if not _url.startswith("http"):
                        continue
                    _rows = get_top_queries_for_url(_gsc, gsc_site_url, _url, top_n=20)
                    for _r in _rows:
                        if "_error" in _r:
                            continue
                        _q = _r["query"].lower()
                        if _q not in _all_queries:
                            _all_queries[_q] = _r
                        else:
                            _all_queries[_q]["impressions"] += _r.get("impressions", 0)
                            _all_queries[_q]["clicks"] += _r.get("clicks", 0)

                _domain_raw = re.sub(r"https?://(www\.)?|sc-domain:", "", gsc_site_url).rstrip("/")
                _domain_parts = set(re.findall(r"[a-z]+", _domain_raw.lower()))
                _domain_parts -= {"com", "net", "org", "co", "uk", "io", "house", "app", "law",
                                   "firm", "group", "inc", "llc", "ltd"}

                _full_name_parts = set(
                    w.lower() for w in re.findall(r"[a-zA-Z]+", full_brand_name)
                    if len(w) >= 3
                )
                _domain_parts = _domain_parts | _full_name_parts

                _detected = {}
                for _q, _r in _all_queries.items():
                    _imp = _r.get("impressions", 0)
                    _clk = _r.get("clicks", 0)
                    _pos = _r.get("position", 99)
                    _ctr = _clk / _imp if _imp > 0 else 0
                    _reasons = []

                    if _ctr >= 0.15 and _imp >= 10:
                        _reasons.append(f"CTR {round(_ctr * 100)}%")
                    if _pos <= 2.0 and _clk >= 5:
                        _reasons.append(f"pos {_pos}")

                    _q_words = set(re.findall(r"[a-z]+", _q))
                    _dom_match = _domain_parts & _q_words
                    if _dom_match:
                        _reasons.append(f"domain word: {', '.join(_dom_match)}")

                    if _reasons:
                        if _dom_match:
                            _root = sorted(_dom_match, key=len)[0]
                        else:
                            _root = _q.split()[0]
                        if _root not in _detected:
                            _detected[_root] = {"queries": [], "reasons": set()}
                        _detected[_root]["queries"].append(_q)
                        _detected[_root]["reasons"].update(_reasons)

                st.session_state["detected_branded"] = _detected

                if not _detected:
                    st.info("No branded terms detected automatically. Use manual entry in the sidebar if needed.")

        if "detected_branded" in st.session_state and st.session_state["detected_branded"]:
            st.caption("Detected branded terms. Checked = will be excluded from keyword scoring.")
            _confirmed = {}
            for _root, _data in st.session_state["detected_branded"].items():
                _reason_str = " | ".join(_data["reasons"])
                _checked = st.checkbox(
                    f"`{_root}` ({_reason_str})",
                    value=True,
                    key=f"brand_chk_{_root}",
                    help=f"Queries excluded: {', '.join(_data['queries'][:5])}"
                )
                if _checked:
                    _confirmed[_root] = _data
            st.session_state["confirmed_branded"] = list(_confirmed.keys())

        elif "detected_branded" not in st.session_state:
            st.caption("Click 'Auto-detect Branded Terms' to scan GSC queries before running.")

    else:
        st.caption("Complete credentials and connect your sheet first.")

    # ── Section 5: Run ────────────────────────────────────────────────────────

    st.header("5. Run")

    ready = (
        sa_file is not None and
        dfs_login and dfs_password and
        ai_key and
        gsc_site_url and
        "df" in st.session_state
    )

    if enable_scraping and not firecrawl_key:
        st.warning("FireCrawl API key is required when page scraping is enabled. Add it in the sidebar or disable scraping.")

    if not ready:
        st.warning("Complete all credentials and settings in the sidebar before running.")

    run_disabled = not ready or (enable_scraping and not firecrawl_key)
    run_btn = st.button("Generate FAQs", type="primary", disabled=run_disabled)

    if run_btn:
        df_work = st.session_state["df"].copy()
        sa_info = st.session_state["sa_info"]
        gsc_client = get_gsc_client(sa_info)

        _manual = [t.strip().lower() for t in branded_terms_input.strip().splitlines() if t.strip()]
        _auto = st.session_state.get("confirmed_branded", [])
        _full_name_words = [
            w.lower() for w in re.findall(r"[a-zA-Z]+", full_brand_name)
            if len(w) >= 3
        ] if full_brand_name.strip() else []
        branded_terms = list(set(_manual + _auto + _full_name_words))

        if branded_terms:
            st.info(f"Branded filter active: {', '.join(sorted(branded_terms))}")

        results = []
        skipped = []
        progress = st.progress(0, text="Starting...")
        total = len(df_work)

        _rate_delays = {
            "Gemini (free)": 5.0,
            "Mistral (free tier)": 2.0,
            "Groq (free tier)": 2.0,
            "Claude": 0.5,
            "OpenAI": 0.5,
        }

        for i, row in df_work.iterrows():
            url = str(row.get(url_col, "")).strip()
            if not url or not url.startswith("http"):
                skipped.append({"row": i + 2, "reason": "Invalid or missing URL"})
                results.append(_empty_result(url, "skipped: invalid URL", num_faqs))
                progress.progress((i + 1) / total, text=f"Row {i + 1}/{total}: skipped")
                continue

            page_type = "general"
            if page_type_col != "(none)":
                pt = str(row.get(page_type_col, "")).strip()
                if pt:
                    page_type = pt

            h1_value = ""
            if h1_col != "(none)":
                h1_raw = str(row.get(h1_col, "")).strip()
                if h1_raw and h1_raw.lower() != "none":
                    h1_value = h1_raw

            # Step 1: Scrape page for topic context
            page_context = ""
            scrape_status = "skipped"
            if enable_scraping and firecrawl_key:
                progress.progress((i + 1) / total, text=f"Row {i + 1}/{total}: scraping page...")
                scrape_result = scrape_page_context(firecrawl_key, url, max_chars=2000)
                if scrape_result["success"]:
                    page_context = scrape_result["content"]
                    scrape_status = f"ok ({len(page_context)} chars)"
                else:
                    scrape_status = f"failed: {scrape_result['error'][:80]}"
                    # Non-fatal: continue with keyword + PAA only

            # Step 2: Keyword selection
            manual_kw = str(row.get(keyword_col, "")).strip() if keyword_col != "(none)" else ""
            selected_keyword = None
            keyword_source = None
            runner_up_kw = None
            kw_volume = None
            kw_difficulty = None

            if manual_kw:
                selected_keyword = manual_kw
                keyword_source = "manual"
            else:
                progress.progress((i + 1) / total, text=f"Row {i + 1}/{total}: fetching GSC data...")
                gsc_queries = get_top_queries_for_url(gsc_client, gsc_site_url, url, top_n=10)

                if gsc_queries and "_error" in gsc_queries[0]:
                    keyword_source = f"fallback: GSC error - {gsc_queries[0]['_error'][:120]}"
                    gsc_queries = []

                if gsc_queries:
                    query_list = [q["query"] for q in gsc_queries]
                    _gsc_debug = ", ".join(
                        f"{q['query']} (pos {q['position']}, imp {q['impressions']})"
                        for q in gsc_queries
                    )

                    progress.progress((i + 1) / total, text=f"Row {i + 1}/{total}: fetching DFS data...")
                    dfs_volumes = get_keyword_overview(dfs_login, dfs_password, query_list, location_code=int(location_code))
                    dfs_difficulty = get_keyword_difficulty(dfs_login, dfs_password, query_list, location_code=int(location_code))

                    dfs_merged = {}
                    for kw in query_list:
                        kw_lower = kw.lower()
                        vol = dfs_volumes.get(kw_lower, {}).get("volume", 0)
                        diff = dfs_difficulty.get(kw_lower, {}).get("difficulty", 50)
                        dfs_merged[kw_lower] = {"volume": vol, "difficulty": diff}

                    result = select_keyword(
                        gsc_queries=gsc_queries,
                        dfs_data=dfs_merged,
                        branded_terms=branded_terms,
                        min_volume=int(min_volume),
                        h1=h1_value
                    )

                    if not result["fallback_triggered"]:
                        selected_keyword = result["selected_keyword"]
                        keyword_source = "gsc+dfs"
                        runner_up_kw = result["runner_up"]["keyword"] if result["runner_up"] else None
                        kw_volume = result["selected_keyword_data"]["volume"] if result["selected_keyword_data"] else None
                        kw_difficulty = result["selected_keyword_data"]["difficulty"] if result["selected_keyword_data"] else None
                    else:
                        non_branded = [
                            q for q in gsc_queries
                            if not any(b in q["query"].lower() for b in branded_terms)
                            and q.get("position", 99) != 1.0
                        ]
                        if non_branded:
                            top_gsc = sorted(non_branded, key=lambda x: x["impressions"], reverse=True)[0]
                            selected_keyword = top_gsc["query"]
                            keyword_source = "gsc-only (low DFS volume)"
                            runner_up_kw = non_branded[1]["query"] if len(non_branded) > 1 else None
                        else:
                            keyword_source = f"fallback: no keyword passed scoring (GSC: {_gsc_debug})"
                else:
                    keyword_source = keyword_source or "fallback: no GSC data"

            if not selected_keyword:
                skipped.append({"row": i + 2, "reason": keyword_source})
                results.append(_empty_result(url, f"skipped: {keyword_source}", num_faqs))
                progress.progress((i + 1) / total, text=f"Row {i + 1}/{total}: skipped ({keyword_source})")
                continue

            # Step 3: Fetch PAA
            progress.progress((i + 1) / total, text=f"Row {i + 1}/{total}: fetching PAA for '{selected_keyword}'...")
            paa_questions = get_people_also_ask(
                dfs_login, dfs_password, selected_keyword, location_code=int(location_code)
            )

            # Step 4: Generate FAQ
            progress.progress((i + 1) / total, text=f"Row {i + 1}/{total}: generating FAQs...")
            try:
                faq_items = generate_faq(
                    provider=ai_provider,
                    api_key=ai_key,
                    keyword=selected_keyword,
                    page_type=page_type,
                    brand_name=brand_name,
                    business_type=business_type,
                    h1=h1_value,
                    paa_questions=paa_questions,
                    num_faqs=num_faqs,
                    forbidden_phrases="\n".join(
                        p.strip() for p in forbidden_phrases.strip().splitlines() if p.strip()
                    ),
                    page_context=page_context,
                )

                schema_jsonld = build_faq_schema(faq_items, page_url=url)

                row_result = {
                    "url": url,
                    "selected_keyword": selected_keyword,
                    "keyword_source": keyword_source,
                    "runner_up": runner_up_kw,
                    "kw_volume": kw_volume,
                    "kw_difficulty": kw_difficulty,
                    "scrape_status": scrape_status,
                    "paa_count": len(paa_questions),
                    "faq_count": len(faq_items),
                    "faq_schema_jsonld": schema_jsonld,
                    "status": "ok"
                }

                for idx in range(num_faqs):
                    if idx < len(faq_items):
                        row_result[f"faq_{idx + 1}_question"] = faq_items[idx]["question"]
                        row_result[f"faq_{idx + 1}_answer"] = faq_items[idx]["answer"]
                    else:
                        row_result[f"faq_{idx + 1}_question"] = ""
                        row_result[f"faq_{idx + 1}_answer"] = ""

                results.append(row_result)

            except Exception as e:
                skipped.append({"row": i + 2, "reason": str(e)})
                results.append(_empty_result(
                    url, f"error: {str(e)}", num_faqs,
                    keyword=selected_keyword, source=keyword_source,
                    scrape_status=scrape_status
                ))

            time.sleep(_rate_delays.get(ai_provider, 0.5))

        progress.progress(1.0, text="Done.")

        results_df = pd.DataFrame(results)
        st.session_state["results_df"] = results_df
        st.session_state["skipped"] = skipped
        st.session_state["total"] = total
        st.session_state["num_faqs"] = num_faqs
        st.rerun()

# ── Results and Export (outside run block so buttons persist across reruns) ──

if "results_df" in st.session_state:
    results_df = st.session_state["results_df"]
    skipped = st.session_state.get("skipped", [])
    total = st.session_state.get("total", len(results_df))
    _num_faqs = st.session_state.get("num_faqs", 5)

    st.header("6. Results")

    ok_count = len(results_df[results_df["status"] == "ok"])
    skip_count = len(skipped)
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Rows", total)
    m2.metric("Generated", ok_count)
    m3.metric("Skipped / Errors", skip_count)

    summary_cols = ["url", "selected_keyword", "keyword_source", "scrape_status", "paa_count", "faq_count", "status"]
    available_summary = [c for c in summary_cols if c in results_df.columns]
    st.subheader("Summary")
    st.dataframe(results_df[available_summary], use_container_width=True, height=300)

    st.subheader("FAQ Preview")
    for _, row in results_df.iterrows():
        if row.get("status") != "ok":
            continue
        with st.expander(f"{row['url']} - {row.get('selected_keyword', '')}"):
            for idx in range(1, _num_faqs + 1):
                q = row.get(f"faq_{idx}_question", "")
                a = row.get(f"faq_{idx}_answer", "")
                if q:
                    st.markdown(f"**Q{idx}: {q}**")
                    st.write(a)
                    st.divider()

            if row.get("faq_schema_jsonld"):
                with st.expander("Schema.org JSON-LD"):
                    st.code(row["faq_schema_jsonld"], language="html")

    if skipped:
        with st.expander(f"Skipped rows ({skip_count})"):
            st.dataframe(pd.DataFrame(skipped), use_container_width=True)

    st.header("7. Export")

    ec1, ec2 = st.columns(2)

    with ec1:
        csv_buffer = StringIO()
        results_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download CSV",
            data=csv_buffer.getvalue(),
            file_name="faq_copy_output.csv",
            mime="text/csv"
        )

    with ec2:
        if st.button("Write Back to Google Sheet"):
            ws = st.session_state["ws"]

            col_map = {
                "selected_keyword": "SEO Target Keyword",
                "keyword_source": "Keyword Source",
                "runner_up": "Runner Up Keyword",
                "scrape_status": "Page Scrape Status",
                "paa_count": "PAA Questions Found",
                "faq_count": "FAQs Generated",
                "faq_schema_jsonld": "FAQ Schema JSON-LD",
                "status": "FAQ Status",
            }
            for idx in range(1, _num_faqs + 1):
                col_map[f"faq_{idx}_question"] = f"FAQ {idx} Question"
                col_map[f"faq_{idx}_answer"] = f"FAQ {idx} Answer"

            with st.spinner("Writing to sheet..."):
                try:
                    write_results_to_sheet(ws, results_df, col_map)
                    st.success(f"Done. {len(results_df)} rows written to Google Sheet.")
                except Exception as e:
                    st.error(f"Write failed: {e}")
                    st.caption(
                        "Common cause: service account does not have Editor access to the sheet."
                    )

