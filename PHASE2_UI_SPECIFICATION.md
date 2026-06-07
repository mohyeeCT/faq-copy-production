# Phase 2: UI Model Selection — Complete Specification

**Status:** Design Document (Ready for Implementation)

---

## Overview

Phase 2 adds a **Model Selection Dropdown** in the sidebar's "AI Provider" section, allowing users to choose which specific model version to use for FAQ generation.

---

## Current UI Structure (Before Phase 2)

```
SIDEBAR
├── Credentials
│   ├── Service Account JSON
│
├── DataForSEO
│   ├── Login (email)
│   └── Password
│
├── Jina Reader
│   ├── Jina API Key
│   └── Enable page scraping [toggle]
│
├── AI Provider              ← Current section
│   ├── Provider [Claude, OpenAI, Gemini, Mistral, Groq]
│   └── API Key [dynamic based on provider]
│
├── Copy Settings
│   ├── Business Type
│   ├── Brand Name
│   ├── Include brand name [checkbox]
│   ├── Full Brand Name
│   ├── Niche
│   └── Brand & Copy Guidelines
│
└── FAQ Settings
    └── ... more options
```

---

## Phase 2 UI Changes

### **Location: Right after "Provider" selectbox**

**Add:** Model Version Selectbox  
**Position:** Between "Provider" and "API Key" input  
**In Code:** After line 137 (after `ai_provider = st.selectbox(...)`)

### **New UI Structure (After Phase 2)**

```
SIDEBAR
├── Credentials
│   ├── Service Account JSON
│
├── DataForSEO
│   ├── Login (email)
│   └── Password
│
├── Jina Reader
│   ├── Jina API Key
│   └── Enable page scraping [toggle]
│
├── AI Provider              ← Updated section
│   ├── Provider [Claude, OpenAI, Gemini, Mistral, Groq]
│   ├── AI Model Version [NEW DROPDOWN]  ← THIS IS NEW
│   └── API Key [dynamic based on provider]
│
├── Copy Settings
│   ├── Business Type
│   ├── Brand Name
│   ├── Include brand name [checkbox]
│   ├── Full Brand Name
│   ├── Niche
│   └── Brand & Copy Guidelines
│
└── FAQ Settings
    └── ... more options
```

---

## UI Component Details

### **Model Version Selectbox**

**Element Type:** `st.selectbox()`

**Label:** `"AI Model Version"`

**Options:** Dynamically change based on provider selection

**Default:** `"Default"`  
(Shows current DEFAULT_MODELS value for that provider in parentheses)

**Placement:** Immediately after Provider selectbox (lines 131-137)

---

## Model Options Per Provider

### Claude Provider
```
Options:
- Default (claude-sonnet-4-6)
- claude-sonnet-4-6
- claude-3-5-sonnet (if available)
[user can only pick from available Claude models]
```

### OpenAI Provider
```
Options:
- Default (gpt-5.5)
- gpt-5.5
- gpt-4o (if user wants to use it)
[available OpenAI models]
```

### Gemini Provider
```
Options:
- Default (gemini-2.0-flash)
- gemini-2.0-flash
- gemini-1.5-pro (if available)
[available Gemini models]
```

### Mistral Provider
```
Options:
- Default (mistral-small-latest)
- mistral-small-latest
- mistral-medium (if available)
[available Mistral models]
```

### Groq Provider
```
Options:
- Default (llama3-70b-8192)
- llama3-70b-8192
- mixtral-8x7b (if available)
[available Groq models]
```

---

## Implementation Details

### **Session State Storage**

```python
# In sidebar, after provider selection:
selected_model = st.selectbox(
    "AI Model Version",
    options=["Default (claude-sonnet-4-6)", "claude-sonnet-4-6"],
    help="Select which model to use. 'Default' uses backend default for this provider."
)

# Store in session state
st.session_state['selected_model'] = (
    None if selected_model.startswith("Default") 
    else selected_model.split(" ")[0]  # extract model name
)
```

### **Passing to FAQ Generation**

**Current Code (lines 538-544):**
```python
batch_results, batch_prompt_sent, batch_page_debug = generate_faq_batch(
    provider=ai_provider,
    api_key=ai_key,
    pages=batch,
    num_faqs=num_faqs,
    include_brand=include_brand,
)
```

**Updated Code:**
```python
batch_results, batch_prompt_sent, batch_page_debug = generate_faq_batch(
    provider=ai_provider,
    api_key=ai_key,
    pages=batch,
    num_faqs=num_faqs,
    include_brand=include_brand,
    model=st.session_state.get('selected_model', None),  # NEW
)
```

**Locations to Update:**
- Line ~538 (batch generation in run_batch_faq)
- Line ~863 (any other batch calls)
- Any single-page FAQ calls (if they exist)

---

## Visual Mockup

### **Sidebar - AI Provider Section (Before)**
```
┌─────────────────────────────────┐
│ 🔑 AI Provider                  │
├─────────────────────────────────┤
│ Provider                        │
│ [Claude ▼]                      │
│                                 │
│ Claude API Key                  │
│ [••••••••••••••••••••]          │
│                                 │
└─────────────────────────────────┘
```

### **Sidebar - AI Provider Section (After Phase 2)**
```
┌─────────────────────────────────┐
│ 🔑 AI Provider                  │
├─────────────────────────────────┤
│ Provider                        │
│ [Claude ▼]                      │
│                                 │
│ AI Model Version                │
│ [Default (claude-so... ▼]       │
│                                 │
│ Claude API Key                  │
│ [••••••••••••••••••••]          │
│                                 │
└─────────────────────────────────┘
```

---

## User Interactions

### **Scenario 1: User keeps default model**
1. User selects provider (e.g., "Claude")
2. Model dropdown defaults to "Default (claude-sonnet-4-6)"
3. User runs FAQ generation
4. Backend uses DEFAULT_MODELS["Claude"] automatically
5. Result: Uses latest recommended model

### **Scenario 2: User selects specific model**
1. User selects provider (e.g., "OpenAI")
2. User changes model dropdown to "gpt-4o" (hypothetical older version)
3. User runs FAQ generation
4. Backend receives `model="gpt-4o"`
5. Result: Uses gpt-4o instead of default gpt-5.5

### **Scenario 3: Provider changes**
1. User selects "Claude" → model dropdown shows Claude models
2. User changes to "OpenAI" → model dropdown updates to show OpenAI models
3. Dropdown resets to "Default" when provider changes
4. Result: Model dropdown always shows correct options

---

## Code Locations to Modify

### **File: app.py**

| Line # | Current Code | Change |
|--------|--------------|--------|
| ~131-137 | `ai_provider = st.selectbox(...)` | Add model selectbox after this |
| ~147 | `ai_key = st.text_input(...)` | Keep as-is |
| ~538-544 | `generate_faq_batch(...)` call | Add `model=...` parameter |
| ~863 | Other batch calls | Add `model=...` parameter if present |

### **File: utils/copy_gen.py**

**No changes needed** — Phase 1 already supports `model` parameter in all functions.

---

## Implementation Checklist

- [ ] Add model selectbox in sidebar (after provider, before API key)
- [ ] Store model selection in session state
- [ ] Pass model to generate_faq_batch() call (line ~538)
- [ ] Pass model to other batch calls if present (line ~863)
- [ ] Test: Verify dropdown shows correct models per provider
- [ ] Test: Verify model parameter is passed to backend
- [ ] Test: Verify FAQ generation works with custom model
- [ ] Test: Verify model changes don't break anything
- [ ] Commit and push to GitHub

---

## Expected User Experience

**Before Phase 2:**
- User selects provider
- App uses whatever model is hardcoded in copy_gen.py
- No control over model version

**After Phase 2:**
- User selects provider
- Model dropdown automatically shows available models for that provider
- User can pick "Default" (recommended) or choose specific model
- Selected model is used for all FAQs in that run
- If model changes mid-run, it applies to subsequent batches

---

## Benefits of Phase 2

✅ **User Control** — Users can pick specific model versions  
✅ **Flexibility** — Can test different models without code changes  
✅ **Future-Proof** — Easy to add new models later  
✅ **Transparency** — Users see which model is being used  
✅ **A/B Testing** — Can compare FAQ quality across models  

---

## Risk Assessment

**Implementation Risk:** Very Low
- Simple UI addition (1 selectbox)
- No backend changes needed
- Phase 1 already has full infrastructure
- Dropdown options don't need to be dynamic (hardcoded list is fine)

**Breaking Risk:** None
- Existing code paths unchanged
- model parameter optional
- Defaults work if dropdown isn't interacted with

**Testing Risk:** Low
- Just verify dropdown appears
- Verify model is passed correctly
- Verify FAQ generation works

---

## Appendix: Model Options Dict

For reference, the model options per provider:

```python
MODEL_OPTIONS = {
    "Claude": [
        ("Default", "claude-sonnet-4-6"),
        ("claude-sonnet-4-6", "claude-sonnet-4-6"),
    ],
    "OpenAI": [
        ("Default", "gpt-5.5"),
        ("gpt-5.5", "gpt-5.5"),
    ],
    "Gemini (free)": [
        ("Default", "gemini-2.0-flash"),
        ("gemini-2.0-flash", "gemini-2.0-flash"),
    ],
    "Mistral (free tier)": [
        ("Default", "mistral-small-latest"),
        ("mistral-small-latest", "mistral-small-latest"),
    ],
    "Groq (free tier)": [
        ("Default", "llama3-70b-8192"),
        ("llama3-70b-8192", "llama3-70b-8192"),
    ],
}
```

---

## Next Steps

1. Review this specification
2. Confirm UI placement and design look good
3. Proceed with implementation
4. Test locally
5. Commit and push to GitHub

