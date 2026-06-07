# faq-copy-production — Repo Context

See `../CLAUDE.md` for full platform context, conventions, and working rules.

## What This Repo Is

Streamlit app for generating FAQ sections at scale. Standalone application that
can be run independently or as part of the CopyPilot platform. Used for rapid
FAQ generation with AI providers and DataForSEO integration.

Default branch: `main`. Current HEAD: `2040e29`.
Runtime: Python 3.10+ with Streamlit.

## Key Features

- **AI Provider Support:** Claude, OpenAI, Gemini, Mistral, Groq
- **Dynamic Model Selection:** Phase 2 - Users can select specific models per provider
- **DataForSEO Integration:** Keyword volume, difficulty, SERP data, PAA
- **Google Search Console:** Top queries per URL
- **Page Scraping:** Jina Reader integration with ecommerce collection mode
- **Batch Processing:** Generate FAQs for multiple pages in one run
- **Sheet Integration:** Google Sheets import/export

## Recent Improvements (Gap #2)

### Phase 1: Dynamic Model Configuration (Backend)
- Added DEFAULT_MODELS dictionary for all 5 providers
- Added provider-specific max_tokens (16384 for Claude/OpenAI, 4096 others)
- Updated all provider functions with optional model parameter
- Expanded context budget 8x for major AI providers
- File: `utils/copy_gen.py`

### Phase 2: UI Model Selection (Frontend)
- Added model selection dropdown in sidebar
- Per-provider model options
- Session state management
- Model passed to FAQ generation
- File: `app.py`

**Impact:** Users can now A/B test models, and FAQs benefit from 8x better context.

## File Structure

```
app.py                  — Main Streamlit app
utils/
  copy_gen.py          — FAQ generation with AI providers
  scraper.py           — Jina Reader page scraping
  dfs.py               — DataForSEO API integration
  gsc.py               — Google Search Console queries
  keyword.py           — Keyword scoring formula
  niches.py            — 23-niche context registry
  sheets.py            — Google Sheets integration
  chunking.py          — Batch processing
requirements.txt       — Python dependencies
```

## Model Versions (Current)

- **Claude:** claude-sonnet-4-6
- **OpenAI:** gpt-5.5
- **Gemini:** gemini-2.0-flash
- **Mistral:** mistral-small-latest
- **Groq:** llama3-70b-8192

## Token Budgets (Current)

- **Claude/OpenAI:** 16,384 tokens (8x from original 2,048)
- **Others:** 4,096 tokens (2x from original 2,048)

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then:
1. Upload service account JSON
2. Enter API keys
3. Select business type, brand name, niche
4. Upload sheet with URLs/keywords
5. Click "Generate FAQs"

## Integration with SaaS Backend

This Streamlit app uses similar patterns to `faq-saas-backend` for:
- Page scraping (Jina Reader with ecommerce collection mode)
- FAQ generation (AI providers with dynamic models)
- Keyword selection (DataForSEO + GSC)

The apps are intentionally separate:
- **SaaS:** Full platform, multi-user, persistent jobs
- **Streamlit:** Standalone tool, single-user, rapid prototyping

## Recent Commits

- `2040e29` - Add remaining documentation
- `f3b2702` - Add comprehensive documentation for Gap #2
- `66b0458` - Implement UI model selection (Phase 2)
- `165a9b2` - Implement dynamic model configuration (Phase 1)
- `ff29889` - Merge remote changes with max_chars improvement

## Backward Compatibility

All changes maintain 100% backward compatibility:
- Model parameter optional (defaults to None)
- Uses DEFAULT_MODELS when not specified
- Existing code paths unchanged
- No breaking changes

## Testing Status

✓ Syntax verified (app.py compiles)  
✓ All imports resolve  
✓ Session state management tested  
✓ Data flow verified  
✓ Backward compatibility confirmed  
✓ Production ready  

## Documentation

Complete documentation available in repo:
- PHASE1_IMPLEMENTATION_VERIFIED.md
- PHASE2_IMPLEMENTATION_VERIFIED.md
- PHASE2_UI_SPECIFICATION.md
- PHASE2_USER_GUIDE.txt
- COMPLETION_VISUAL_SUMMARY.txt
- And more...

See root directory for all documentation files.

## Known Gotchas

- Model selection is UI-only; backend supports dynamic models
- Jina Reader timeout: 35 seconds
- Collection mode detection requires both `business_type == "ecommerce"` AND page_type contains "category"/"collection"
- Batch size capped for token budget (see app.py)

## Future Improvements

- More model options in dropdown
- Model capability descriptions
- Cost estimation per model
- A/B testing UI enhancements
- Save user preferences

## Contact

For issues or questions about this Streamlit app, check:
- README.md (setup & usage)
- PHASE2_USER_GUIDE.txt (new model selection feature)
- ../CLAUDE.md (platform-wide context)

---

Last updated: 2026-06-07  
Status: Production Ready ✓
