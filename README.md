# FAQ Copy Production

Streamlit app for generating FAQ sections at scale using People Also Ask data from DataForSEO + GSC keyword selection + AI.

## Setup

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Google Service Account

Same service account used for both Google Sheets and GSC access.

1. Go to Google Cloud Console > IAM > Service Accounts
2. Create a service account and download the JSON key
3. Share your Google Sheet with the service account email (Editor access)
4. Add the service account email as a verified user in GSC (Search Console > Settings > Users and permissions)

### 3. Run

```
streamlit run app.py
```

---

## Input Sheet Format

| URL | Keyword (optional) | Page Type (optional) | H1 (optional) |
| --- | --- | --- | --- |
| https://example.com/page | water softener | product | Best Water Softeners for Home |

- **URL**: Required
- **Keyword**: Optional. If blank, the app uses the GSC + DFS keyword pipeline
- **Page Type**: Optional (product, category, blog, landing, etc.)
- **H1**: Optional. Used as context for FAQ generation

---

## Keyword Pipeline

1. Manual keyword in sheet takes priority
2. Pull top 10 GSC queries for the URL
3. Score using DataForSEO volume + difficulty
4. Select highest-scoring non-branded query
5. GSC-only fallback if DFS returns zero volume

---

## PAA Pipeline

Once the target keyword is selected:
1. Call DataForSEO SERP organic live advanced with the keyword
2. Extract all `people_also_ask` items from the SERP results (up to 8 questions)
3. Pass questions to AI as seed questions for the FAQ
4. If no PAA data returns, AI generates questions from keyword + page context

---

## Output Columns Written to Sheet

| Column | Description |
| --- | --- |
| SEO Target Keyword | Keyword used for copy generation |
| Keyword Source | manual / gsc+dfs / fallback reason |
| Runner Up Keyword | Second-best keyword candidate |
| PAA Questions Found | Count of PAA questions retrieved from DFS |
| FAQs Generated | Count of Q&A pairs generated |
| FAQ 1 Question ... FAQ N Question | Individual FAQ questions |
| FAQ 1 Answer ... FAQ N Answer | Individual FAQ answers |
| FAQ JSON | All Q&A pairs as a JSON array |
| FAQ Status | ok / skipped / error |

---

## DFS Location Codes

- 2840 = United States
- 2826 = United Kingdom
- 2036 = Australia
- 2124 = Canada

Full list: https://docs.dataforseo.com/v3/appendix/locations/
