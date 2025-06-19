# Better French – AI-Engine v3 🍷🇫🇷

Single-repository, end-to-end pipeline that fetches French news, filters & scores it with a rules + LLM blend, then publishes a lightweight static website every hour.

This README is the **source-of-truth handbook** for any future engineer (human or LLM) joining the project.

---
## 0.  Repo & branch layout

| Branch | Purpose |
|--------|---------|
| **ai-engine-v3-main** | Active development + production. All CI and deploys run from here. |
| main (legacy) | Frozen v2 code kept only for reference. |

### Directory map (v3)

```
ai_engine_v3/
  ├─ pipeline/              # shared helpers (scraper, curator, utils)
  ├─ scripts/               # thin CLI wrappers – importable as modules
  ├─ website/               # static site, built by Netlify
  ├─ data/                  # runtime state & caches
  └─ tests/                 # unit + integration tests
```

---
## 1.  Hourly production loop

```mermaid
graph TD;
  GH["GitHub Action<br/>auto_update_v3.yml<br/>(*hourly*)"] -->|PYTHONPATH=. python -m ai_engine_v3.scripts.fetch_news| F[Fetch]
  F --> Q[Qualify]
  Q -->|writes JSON| Site[website/rolling_articles.json]
  Q -->|commit & push| GH
  GH --> Netlify[Netlify build]<br/>(triggered on push)
  Netlify --> LiveSite[https://ephemeral-florentine-48f9c7.netlify.app]
```

* **Fetch** – `scripts.fetch_news` scrapes ~25 RSS feeds, dedups via cache, stores new raw articles under `data/raw_archive/` and writes a *_delta.json file (only today's changes).
* **Qualify** – `scripts.qualify_news`:
  1. Loads only *_delta.json files (state keeps track).
  2. Hard filters with rule-based CuratorV2 (env-var `BF_MIN_RULE_SCORE`).
  3. Calls `relevance_llm.py` (Claude-Sonnet via OpenRouter) for nuanced scoring.
  4. Applies bucket balancing & daily cap (`BF_DAILY_CAP`, default 20).
  5. Converts to `Article` schema and writes:
     • `website/rolling_articles.json`
     • Archives under `website/04_Data_Output/`.
  6. Commits with message `🤖 Auto-update v3: fresh articles & site feed`.

---
## 2.  Configuration

| Item | Location / Env var | Notes |
|------|-------------------|-------|
| OpenRouter API key | `OPENROUTER_API_KEY` (GitHub + local `.env`) | Required for LLM scoring. |
| Rule threshold | `BF_MIN_RULE_SCORE` | default 14.0 |
| Daily cap | `BF_DAILY_CAP` | default 20 |
| Per-run cap | `BF_PER_RUN_CAP` | set to 5 by the hourly Action |

Runtime state lives in `ai_engine_v3/data/state.json`:

```jsonc
{ "date": "2025-06-19", "published_today": 25 }
```

---
## 3.  CI / GitHub Actions

| Workflow file | Name in UI | What it does |
|---------------|-----------|--------------|
| `.github/workflows/ci.yml` | **v3-ci** | lint with Ruff, run tests, and a 1-article smoke pipeline on every push & PR. |
| `.github/workflows/auto_update_v3.yml` | **Auto Update French News – v3** | Hourly cron job that runs the full pipeline and commits results. Requires `contents: write` permission. |
| `.github/workflows/qa.yml` | **QA Smoke Test** | Cypress visual regression against production once per day. |

All legacy v2 workflows have been stubbed out (empty `on:` + `noop`) so they no longer appear in Actions.

---
## 4.  Netlify deploy

* **Site ID**  `c482cb0d-1ae5-4986-97e8-09948ae2eb3e`
* **Production branch**  `ai-engine-v3-main`
* **Publish directory**  `ai_engine_v3/website`

Changes are made in the UI under *Build & deploy → Continuous deployment*.  Netlify also honours `netlify.toml`, but we keep the UI in sync to avoid confusion.

### Local preview

```bash
PYTHONPATH=. python3 scripts/run_v3_pipeline.py --serve
# → serves http://localhost:8010/ with live data
```

---
## 5.  Development workflow

1. Create feature branch off `ai-engine-v3-main`.
2. Write code + tests.
3. `pre-commit run -a` for Ruff / black / isort.
4. Push → CI must pass.
5. Open PR → once merged the hourly Action will include your changes.

---
## 6.  On-boarding checklist for new LLMs

1. Export secrets locally:
   ```bash
   export OPENROUTER_API_KEY="sk-or-..."
   ```
2. `pip install -e ./ai_engine_v3[dev]` (editable install)
3. Run unit tests: `pytest -q tests/ai_engine_v3`
4. `python -m ai_engine_v3.scripts.fetch_news` → produces raw file.
5. `python -m ai_engine_v3.scripts.qualify_news` → writes website files.
6. `python -m http.server 8010 -d ai_engine_v3/website` → open browser.

Happy hacking — and bienvenue à Better French 🇫🇷!

## TODO – contextual-word backfill

**Temporary change (20 Jun 2025):**
We relaxed the display-ready rule in `processor.py` so that *any* article with
simplified titles + summaries is immediately shown on the website, even if the
contextual-word coverage is incomplete.

**Next step (tracked as an issue):**
1. Reinstate a stricter coverage threshold (≥ 80 %, maybe 90 %).
2. Add an asynchronous "backfill" job that revisits pending articles lacking
   coverage and re-prompts the LLM until they pass.
3. Only downgrade to the relaxed rule if after two attempts coverage is still
   insufficient.

This note is a reminder to implement that backfill strategy before EOM. 