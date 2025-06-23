# Prompt Research Brief – Contextual Words & Simplified Titles (v3)

Last updated: 2025-06-23

## 1. Product background
Better French is a news-digest site for intermediate French learners.  Each headline card shows:
1. A simplified French headline + English translation plus 2-sentence summaries.
2. Hoverable tool-tips on every non-trivial token in the French headline (word, idiom or proper name) – learners can read a concise English gloss + cultural note.

The prompts that generate those enhancements live in `ai_engine_v3/prompts/`.
Current production files (`*_v2.jinja`) work but have shortcomings: inconsistent token coverage, occasional French headings, verbosity.

We want **v3** prompts that maximise:
* 100 % coverage – one JSON object per token supplied by the processor.
* Heading correctness – the bold English heading must be an idiomatic 1-3-word translation, never French.
* Compactness – explanations ≤ 20 words (CEFR-B1), optional cultural note ≤ 25 words.
* JSON validity – no markdown wrappers, no key drift.

## 2. What you will deliver
1. Edit **`contextual_words_v3.jinja`** – generates tool-tip array.
2. Edit **`simplify_titles_summaries_v3.jinja`** – generates simplified titles + 2× summaries.
3. Add unit-test cases under `qa/local/` that prove the new prompts meet the success criteria.

Avoid touching the existing `*_v2` files – they remain the production fallback.

## 3. Hard constraints
* Must return valid JSON (array for contextual words, object for titles) – nothing else.
* Schema keys and their order cannot change.
* When the processor supplies `TOKENS_TO_DEFINE`, you must return **exactly one** item for every token in that list and in the same order.
* Length caps (20-27 word summaries, ≤ 20-word explanations) are enforced by downstream validator – exceeding them will discard the article.

## 4. Soft goals / style guide
* Tone: neutral textbook English; avoid slang unless it clarifies meaning.
* Cultural notes optional – include only if the token needs extra background (e.g. French institutions, historic events).
* Use CEFR-appropriate vocabulary (B1-B2).
* Prefer everyday English headings over literal cognates (e.g. **Prime Minister** not **Premier Ministre**).

## 5. Example call-and-response
Input variables provided to the template engine:
```yaml
{
  "title": "Macron annonce un plan "razzia" contre la fraude fiscale",
  "tokens": ["Macron", "annonce", "plan", "razzia", "fraude", "fiscale"]
}
```
Expected output (spacing/ordering simplified):
```json
[
  {"original_word":"Macron","display_format":"**Macron:** Macron","explanation":"French President (2017-present)","cultural_note": ""},
  {"original_word":"annonce","display_format":"**Announces:** annonce","explanation":"3rd-person singular of 'annoncer' (to announce)","cultural_note":""},
  … etc …
]
```

## 6. Evaluation & hand-off
Run `pytest qa/local` – all new tests must pass.  We'll also run a 24 h shadow deployment that records validator pass-rate vs. v2.

Commit your changes on branch **`prompt-research`** (already exists) and open a PR to `ai-engine-v3-main`.

Thanks!  
— Better French engineering 