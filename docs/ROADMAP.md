# Better-French – Roadmap (v3 era, updated June 2025)

_This is the high-level **where-we-re-going** document.  For the granular, always-changing backlog see `docs/future_features.md`._

---

## 0  Snapshot – what's already shipped in v3

| Date | Delivery | Notes |
|------|----------|-------|
| 31 May 2025 | **AI-Engine v3 in production** | Hourly GitHub Action scrapes → curates → AI-enhances → commits to `ai_engine_v3/website` and Netlify auto-deploys. |
| 12 Jun 2025 | **Contextual-word validation fixes** | Model accepts dict or list; live feed now shows >100 underlined words. |
| 16 Jun 2025 | **Repository clean-up** | Removed all v2 code, legacy scripts, large root `data/` folder. |
| 19 Jun 2025 | **Raw-archive refactor** | Hourly deltas stored under `ai_engine_v3/data/raw_archive/` (local only). |
| 20 Jun 2025 | **CI + pre-commit hook enforced** | Daily note check & Ruff lint run on every PR. |
| 21 Jun 2025 | **QA suite (Playwright + Axe + visual diff)** | Smoke tests run on PR via `qa.yml`. |

---

## 1  Branch strategy  
_We now run a single trunk-based flow._

| Branch | Purpose |
|--------|---------|
| `ai-engine-v3-main` (default) | All normal work; hourly pipeline points here. |
| feature branches | Short-lived, named `feat/<topic>`; merge via PR. |

Large/risky changes (schema bumps, infra) get a design doc in `docs/proposals/` before coding.

---

## 2  Near-term feature waves (Q3 2025)

### Wave 1 – Site reliability & feedback (target **July**)  
1. **MCP server v2** – health endpoints `/status`, `/advice`, `/chat`  
2. **One-click tooltip feedback** – Netlify Function writes `config/manual_overrides.json`  
3. **Playwright UI checker bot** – Percy visual snapshots + Axe in CI  
4. **Backup pruning** – keep last 200 `rolling_*.json` files

### Wave 2 – Storage & performance (target **August**)  
1. **Supabase raw-archive** – upload hourly deltas, keep 30-day local cache  
2. **Lighthouse performance budget** – fail PR when CWV drop below threshold  
3. **TTS prototype** – ElevenLabs MP3 generation & play-button

### Wave 3 – Personalisation (target **September**)  
1. **Personalised ranking service** (`personaliser.py`)  
2. **UI filters** – difficulty dropdown, tone chips, tag cloud  
3. **Email digest MVP** – top 5 personalised articles per week

> Detailed WHAT / WHY / HOW for each item lives in `future_features.md`.

---

## 3  Tentative timeline

| Month | Key milestone |
|-------|---------------|
| **July 2025** | MCP v2 live; tooltip feedback closed beta |
| **Aug 2025** | Supabase storage; audio TTS alpha; perf budget in CI |
| **Sep 2025** | Personalised ranking & UI filters → public beta |
| **Oct 2025** | Mobile-first design sprint + push-notification PWA |

Dates are aspirational; quality trumps calendar.

---

## 4  Success metrics
1. **Feed freshness** – ≥100 display-ready articles at all times.  
2. **Tooltip accuracy** – <2 % user-flagged errors per week.  
3. **CI health** – `main` green >95 % of the time.  
4. **Performance** – LCP ≤2.5 s on mobile, CLS ≤0.1.

---

## 5  How to contribute

1. Read `CURSOR_RULES.md` (assistant + human workflow).  
2. Create/append today's note in `docs/daily_notes/`.  
3. Small PRs; link to a proposal if touching >10 files.  
4. Keep **roadmap checkboxes** up-to-date when work lands.

---

_Last edit: 21 June 2025_ 