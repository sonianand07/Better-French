# DeepResearch Assignment – Designing Robust Prompts for "Better French"

Version: 2025-06-23

---
## 1 · Product snapshot
Better French is a daily news digest designed for **intermediate French learners (CEFR B1-B2)** who did _not_ grow up in France.  For each article we show:

1. A headline rewritten in simpler French **plus** an English translation and two short summaries (one FR, one EN).
2. Hover-tips on every non-trivial French word, idiom or proper noun in the headline.  Each tooltip displays:  
   **Heading** (bold English translation) · _explanation_ (≤ 20 words) · _optional cultural note_ (≤ 25 words).

All tool-tips and summaries are produced by two system prompts that call an LLM.  You will design **new, production-grade prompts** that outperform the current baseline.

---
## 2 · Pain-points with the current prompts
1. **Incomplete coverage** – when we pass a list of tokens the model sometimes returns only 60-80 % of them.
2. **French headings** – occasionally the model bolds the original French word instead of an English gloss.
3. **Violations of length / JSON rules** – stray markdown fences, extra keys, explanations > 20 words.
4. **Verbosity in summaries** – French & English summaries exceed 27 words or drift off-topic.

Our validator discards any article that fails these rules, so missing tokens or invalid JSON directly reduces website content.

---
## 3 · Your mission
Create **two new prompts**:

| Prompt file (to supply) | Purpose |
|-------------------------|---------|
| `contextual_words_prompt.txt` | Generate the tooltip array. |
| `simplify_titles_prompt.txt`  | Generate simplified titles + summaries. |

Both prompts must be _self-contained_ – assume they will be filled with variables using a template engine similar to Jinja2.

### 3.1  Variable contract
The runtime code will render each prompt with the following dictionary:
```jsonc
{
  "title": "Original French headline as a single string",
  "tokens": ["list", "of", "string", "tokens"]   // *tooltip prompt only* – may be 0-30 items, preserve order
}
```
If `tokens` is an empty list you may choose the 3-10 most important tokens yourself.

### 3.2  Required output schema
####  A) Tooltip prompt
Return a JSON **array** – _nothing else_ – where each element is:
```jsonc
{
  "original_word": "string",              // token exactly as it appears in the headline
  "display_format": "string",             // **EnglishHeading:** French original (≤4 French words)
  "explanation": "string",                // ≤20 plain-English words, B1 vocabulary
  "cultural_note": "string or null"        // optional, ≤25 words
}
```
Constraints:
* 1-to-1 mapping with `tokens` (same order, no extras, no omissions) when the list is provided.
* Heading (**bold part of `display_format`**) must be an English translation, never French unless spelling is identical in both languages.

####  B) Titles & summaries prompt
Return a JSON **object** with exactly these keys in this order:
```jsonc
{
  "simplified_french_title": "≤60 chars",
  "simplified_english_title": "≤60 chars",
  "french_summary":  "20-27 words",
  "english_summary": "20-27 words",
  "difficulty": "A1|A2|B1|B2|C1|C2",
  "tone": "neutral|opinion|satire|other"
}
```
Guidelines: keep neutral tone unless original headline is clearly opinionated; use CEFR-appropriate vocabulary; no lists or bullet points.

---
## 4 · Success metrics
Your prompts will be evaluated on a held-out set of 200 real headlines.

| Metric | Target |
|--------|--------|
| JSON validity pass-rate | ≥ 99 % |
| Token coverage (tooltip) | 100 % of supplied tokens present |
| English-heading correctness | ≥ 98 % (manual check sample) |
| Length compliance | ≥ 98 % |
| Reviewer usefulness score | ≥ 4 / 5 average |

A failure in any hard constraint is an automatic rejection.

---
## 5 · Deliverables & hand-off
1. `contextual_words_prompt.txt` and `simplify_titles_prompt.txt` (UTF-8, no BOM).  
   Placeholders should use the syntax `{{title}}` and `{{tokens}}` so we can adapt to any engine.
2. `test_cases.json` – optional: a small set of headline + token lists you used while iterating.
3. A brief rationale (max 1-page) explaining your design choices.

Please upload the three files in your DeepResearch portal task. Our engineers will integrate them into the pipeline and run the evaluation suite.

---
## 6 · Reference example
_Input_
```json
{"title":"Macron annonce un plan \"razzia\" contre la fraude fiscale","tokens":["Macron","annonce","plan","razzia","fraude","fiscale"]}
```
_Output (excerpt)_
```json
[
  {"original_word":"Macron","display_format":"**Macron:** Macron","explanation":"President of France (2017–present)","cultural_note":""},
  {"original_word":"annonce","display_format":"**Announces:** annonce","explanation":"Third-person singular of 'annoncer' (to announce)","cultural_note":""},
  …
]
```
---
Questions?  Email ​tech@betterfrench.io 