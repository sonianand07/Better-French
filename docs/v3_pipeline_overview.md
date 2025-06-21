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

---

## 11. Environment variables & config flags

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENROUTER_API_KEY` | **required** | Auth token for all LLM calls |
| `BF_PER_RUN_CAP` | `20` | Max articles published each hourly run |
| `BF_DAILY_CAP` | `999999` | 24-h publication ceiling |
| `BF_MIN_RULE_SCORE` | `12` | Curator rule threshold |
| `BF_MODEL_PRIMARY` | `mistralai/mistral-medium-3` | Override default model |
| `BF_MODEL_FALLBACK` | `google/gemini-2.5-flash` | Used if primary slug invalid |
| `BF_SITE_URL` | `https://better-french.netlify.app` | For link generation in future emails |

Values can go in **`config/config.ini`** for local runs; CI sets them via workflow `env:` block.

---

## 12. LLM pricing model (as of 2025-06-20)

| Model | Input / 1k | Output / 1k | Used for |
|-------|------------|-------------|----------|
| `mistralai/mistral-medium-3` | $0.00040 | $0.00200 | Main processor (titles + vocab) |
| `mistralai/mistral-large-2411` | $0.00200 | $0.00600 | Relevance scorer |
| `google/gemini-2.5-flash` | $0.00025 | $0.00050 | Fallback |

`processor._estimate_cost()` keeps a running total; the workflow prints cost per batch in the logs.

---

## 13. File-naming conventions

* **Raw deltas** – `YYYYMMDD_HHMMSS_delta.json` under `raw_archive/DATE/`
* **Full scrape** – `raw_scrape_YYYYMMDD_HHMMSS.json`
* **Rolling feed backup** – `website/backups/rolling_YYYYMMDD_HHMMSS.json`
* **Curated rejects** – `data/live/rejected_articles_TIMESTAMP.json` (rare)

Timestamps are UTC to avoid daylight-savings confusion.

---

## 14. Netlify & domain

* `netlify.toml` lives at repo root → Netlify auto-detects; publish dir is `ai_engine_v3/website`.
* No build command; it simply serves static files.
* Custom domain can be added via Netlify UI – SSL is provisioned automatically.

---

## 15. Extending the system

1. **Add a new RSS source**  → Append to `feed_urls` dict in `scraper.py`; push.
2. **Change curator rules**   → Tweak weights in `curator_v2.py` or adjust `BF_MIN_RULE_SCORE`.
3. **New LLM fields**        → Update `models.Article`, prompts, website template.
4. **Personal e-mail digests**→ Build a small FastAPI endpoint in `mcp_server/` that emails the latest rolling feed nightly.
5. **Mobile app**             → Consume `rolling_articles.json` directly; same schema.

---

## 16. Quick glossary (file → meaning)

| Path | Meaning |
|------|---------|
| `ai_engine_v3/data/state.json` | Tracks `last_delta` processed and per-day publish count |
| `ai_engine_v3/data/live/pending_articles.json` | Queue awaiting AI enhancement |
| `ai_engine_v3/data/live/overflow.json` | Articles held for future runs |
| `ai_engine_v3/data/_cache/visited_hashes.json` | SHA-1 of links seen in raw scrape (dedup) |
| `ai_engine_v3/website/rolling_articles.json` | What Netlify serves |

---

> **This overview is meant to be living documentation.**  If you touch any piece of the pipeline, append your changes here in the relevant section so future contributors (human or AI) stay in sync.