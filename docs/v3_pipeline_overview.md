# Better French – AI-Engine v3 Technical Overview

_Last updated: 2025-06-21_

---

## 1. Product purpose

Better French helps non-native residents of France keep up with national news **and** learn the language at the same time.  We turn French RSS feeds into bite-sized, learner-friendly articles that include:

* simplified French & English titles
* a short bilingual summary
* contextual vocabulary tool-tips
* CEFR difficulty and tone tags

V3 fully automates the process: hourly scraping, rule-based curation, LLM processing, and instant publishing to Netlify.

---

## 2. End-to-end data flow

```mermaid
flowchart TD
    A[RSS feeds (25 sources)] --> B[SmartScraper]
    B --> C[raw_archive (JSON)]
    B --> D[CuratorV2]
    D -->|quality + importance + breaking rules| E[qualify_news]
    E --> F[LLM relevance score]
    F -->|top N| G[pending_articles.json]
    G --> H[ProcessorV2 (LLM prompts)]
    H --> I[rolling_articles.json]
    I --> J[Netlify deploy]
```

---

## 3. Key code modules

| File | Responsibility |
|------|----------------|
| `ai_engine_v3/pipeline/scraper.py` | multithread RSS fetch, dedup, breaking-news flag |
| `ai_engine_v3/pipeline/curator_v2.py` | rule filter: quality, importance, source reputation |
| `ai_engine_v3/scripts/fetch_news.py` | run scraper every hour, write day-deltas to **raw_archive/** |
| `ai_engine_v3/scripts/qualify_news.py` | merge deltas ⇒ curator ⇒ LLM relevance ⇒ choose batch |
| `ai_engine_v3/processor.py` | two-step LLM chat (titles & vocab) |
| `ai_engine_v3/storage.py` | save pending / rolling, backup before overwrite |
| `.github/workflows/auto_update_v3.yml` | hourly CI that chains the two scripts + commit |

---

## 4. Data directories

```
ai_engine_v3/
│
├─ data/
│   ├─ live/               # pending queue + overflow + visited_hashes
│   ├─ raw_archive/        # raw RSS deltas (ignored by Git)
│   └─ state.json          # daily publish counter
│
└─ website/
    ├─ rolling_articles.json      # live feed (max 100 latest)
    └─ backups/rolling_*.json     # auto-backup per run
```

> The legacy root-level `data/` folder has been removed.

---

## 5. Prompt templates

### 5.1 Titles & summaries (`prompts/simplify_titles_summaries.jinja`)
```txt
System: You are Better French AI assistant.
User:
Title: "{{ title }}"
Provide JSON with keys:
  simplified_french_title (≤65 chars),
  simplified_english_title,
  french_summary (≤45 words),
  english_summary,
  difficulty (A1-C2),
  tone (neutral/opinion/satire/other)
```

### 5.2 Contextual words (`prompts/contextual_words.jinja`)
```txt
Goal: help learners decode every word.
Return pure JSON **array**.
For each token give:
  original_word,
  display_format,
  explanation (≤20 English words),
  cultural_note
NAME RULE: consecutive capitalised words = one token.
```

Processor converts the returned array to a dict keyed by `original_word` for website consumption.

---

## 6. Curation logic (qualify_news)

1. Load new delta files newer than `state.json.last_delta`.
2. Rule filter: `total_score ≥ $MIN_RULE_SCORE` (env, default 12).
3. Skip links already on the site.
4. LLM relevance score → blended = 0.6 * total + 0.4 * rel.
5. Respect caps:
   * per-run `BF_PER_RUN_CAP` (default 10 in CI, 20 in prod).
   * daily `BF_DAILY_CAP` (env, default unlimited).
6. Spillover goes to `overflow.json` (24-hour TTL).

---

## 7. Deployment workflow

* **Schedule** – hourly at minute 0.  Env-var caps ensure cost control.
* **Pre-commit hook** now runs in CI → workflow fails if daily note missing.
* Netlify just serves `ai_engine_v3/website/`; no build step.

---

## 8. Improvement opportunities

| Area | Idea |
|------|------|
| Prompt quality | Expand explanation word-limit; request pronunciation keys; add TTS audio generation |
| Data retention | Push raw_archive to Supabase bucket; keep only 30 days locally |
| Backups | Auto-prune rolling_*.json backups to last 200 runs |
| Relevance model | Switch from Mistral-Large to Claude-Sonnet if budgets allow |
| UI tests | Implement Playwright checker described in `ai_ui_checker_overview.md` |
| Personalisation | Use `personaliser.py` to generate user-specific rankings |

---

## 9. Running locally

```bash
# one-off
pip install -r requirements.txt
pip install -e ./ai_engine_v3

# fetch + qualify + process + serve
OPENROUTER_API_KEY=sk-xxx python -m ai_engine_v3.pipeline.runner --limit 20 --serve
```

Hourly simulator:
```bash
watch -n 3600 "python -m ai_engine_v3.scripts.fetch_news && \ 
               python -m ai_engine_v3.scripts.qualify_news"
```

---

## 10. Research context

Better French bridges the gap between classroom apps (Duolingo) and real-world content.  Learners read current French news, enriched with instant glossary pop-ups, so they acquire vocabulary & context simultaneously.

---

### Maintainers
*Human*: @[your-github]  |  *Assistant*: ChatGPT-4o 