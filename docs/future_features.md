<!--
❗ BACKLOG MAINTENANCE RULES (read before editing)
• File: docs/future_features.md – single source for product-level features.
• Four table columns (ID, Feature, Brief, Status) – no extra columns, no blank rows.
• Use <br/> for line-breaks inside cells; keep |----| separator length.
• Allowed Status values: ❌ Pending, 🚧 In Progress, ✅ Done, 🛑 Blocked.
• Each ID must have a WHAT/WHY/HOW detailed brief below.
• When feature ships, move its row to 'Done' table and archive/remove its brief.
-->

# Future Features Backlog

A central, living list of ideas **not yet implemented** for AI-Engine v3 and the Better-French site.  When a feature ships, move it to the _Done_ section or delete it.

| ID | Feature | Brief | Status |
|----|---------|-------|--------|
| F-001 | **MCP server v2** | Live health checker:<br/>fetch feed, run checks,<br/>REST `/status` `/advice` `/chat` | ❌ Pending |
| F-002 | One-click feedback loop | Tooltip editor +<br/>`manual_overrides.json` patch<br/>auto-injected in pipeline | ❌ Pending |
| F-003 | Playwright UI checker bot | Headless tests + Percy<br/>visual snapshots + Axe WCAG | ❌ Pending |
| F-004 | Supabase raw archive | Hourly raw deltas → bucket;<br/>keep 30-day local cache | ❌ Pending |
| F-005 | Audio TTS (ElevenLabs) | Generate French MP3,<br/>add `audio_url`, play-button | ❌ Pending |
| F-006 | Personalised ranking | FastAPI ranks feed by<br/>user profile & behaviour | ❌ Pending |
| F-007 | UI filters | Difficulty dropdown,<br/>tone chips, topic tags | ❌ Pending |
| F-008 | Backup pruning | Keep newest 200 backups,<br/>delete older automatically | ❌ Pending |
| F-009 | Lighthouse perf budget | CI fails PR if web-vitals<br/>drop below budget | ❌ Pending |
| F-010 | Context block for contextual words | Summary + key facts (≤200 tokens) fed to LLM for higher-quality tool-tips | ❌ Pending |

## Done

| Feature | Commit / PR |
|---------|-------------|
| Raw-archive moved inside `ai_engine_v3/data/` | a6d5c00 |
| Pre-commit hook enforced in CI | 4084071 |

### Detailed briefs

#### F-001 MCP server v2 – live-site health & advice
**WHAT**  
A standalone micro-service (Modal-Context Protocol) that continuously pulls the production `rolling_articles.json`, validates it against the latest Pydantic schema and serves three endpoints:  
• `/status` – current health metrics<br/>• `/advice` – actionable remediation tips<br/>• `/chat` – Q&A over the dataset & metrics

**WHY**  
• Eliminates blind spots when the public feed goes stale or malformed.  
• Enables user-friendly status banners on the website and Slack/Email alerts.  
• Forms the foundation for future admin dashboards.

**HOW**  
1. FastAPI + Pydantic v2, packaged in Docker; deploy to Fly.io.  
2. APScheduler job every 5 min fetches Netlify URL, computes metrics, stores SQLite/Redis cache.  
3. Reuse validation rules in `ai_engine_v3/validator.py`.  
4. GitHub Action contract test hits preview URLs.  
5. SLA: < 200 ms P95 latency, 99.9 % uptime.

#### F-002 One-click feedback loop for tool-tips
**WHAT**  
In-page editor lets approved translators fix vocabulary/tool-tip text; patches stored in `config/manual_overrides.json` and injected by the processor.

**WHY**  
• Crowdsources linguistic accuracy.  
• Converts multi-step PR workflow into a few seconds.

**HOW**  
Front-end pencil icon → POST `/api/override` (Netlify Function) → commit override → pipeline re-runs.  
Secure with Netlify Identity. Unit tests with Cypress.

#### F-003 Playwright UI checker bot
**WHAT**  
Headless tests that take Percy snapshots & run Axe accessibility audits on each PR.

**WHY**  
• Catches visual or WCAG regressions early.

**HOW**  
GitHub Action with Playwright matrix (Chrome/dark-mode). Thresholds: visual diff < 0.1 %, 0 new Axe critical issues. Update-snapshot workflow for intentional design changes.

#### F-004 Supabase raw-archive storage
**WHAT**  
Uploads hourly raw scraped deltas to Supabase object storage; keep only last 30 days locally.

**WHY**  
• Prevents repo/CI bloat.  
• Enables SQL-style analytics.

**HOW**  
Create bucket `raw_archive`; signed URLs (7 days). Extend `fetch_news.py` to `supabase.upload()`. Cleanup job prunes local files older > 30 days. Backfill script available.

#### F-005 Audio TTS (ElevenLabs)
**WHAT**  
Generates French MP3 per article, adds `audio_url` to JSON and play-button on site.

**WHY**  
• Multi-modal learning boosts comprehension.  

**HOW**  
`processor.generate_tts()` with hash-cache. Respect daily credit cap via env var. Lazy-load `<audio>` on click.

#### F-006 Personalised ranking
**WHAT**  
Ranks feed per user profile via LightGBM/implicit-ALS model served by `personaliser.py`.

**WHY**  
• Higher engagement; groundwork for premium adaptive curriculum.

**HOW**  
Nightly trainer writes `model.bin`. FastAPI endpoint `POST /rank` returns ordered list. A/B test vs control; metrics: dwell-time lift.

#### F-007 UI filters
**WHAT**  
Difficulty dropdown, tone chips, tag cloud filter client-side.

**WHY**  
• Reduces cognitive overload, improves focus.

**HOW**  
Expose `difficulty`, `tone`, `tags` in JSON. Svelte store filters reactively; persist to `localStorage`. QA test ensures filter correctness.

#### F-008 Backup pruning
**WHAT**  
Keeps only newest 200 `rolling_*.json` backups.

**WHY**  
• Avoids thousands of files slowing Netlify uploads.

**HOW**  
Hourly CI step: `ls -1t backups/rolling_*.json | tail -n +201 | xargs rm`. Dry-run in dev.

#### F-009 Lighthouse performance budget
**WHAT**  
Lighthouse-CI in GitHub Actions that fails PRs when core web vitals drop below budget.

**WHY**  
• Guarantees snappy UX on low-end devices.

**HOW**  
Add `treosh/lighthouse-ci-action`; budgets in `qa/`. Report trends on GitHub Pages; "override" label to bypass temporarily.

#### F-010 Context block for contextual words – richer LLM input
**WHAT**  
Generate a concise context block (~120-200 tokens) per article (summary + key facts) and pass it alongside the headline to the contextual-words prompt.

**WHY**  
• Gives the LLM enough background to disambiguate names, idioms and metaphors without the cost of full-article input.  
• Expected to reduce vague placeholders and improve gloss accuracy.

**HOW**  
1. Add `context_block: str` field to `Article` model.  
2. New pipeline stage: LLM summariser (≤80 words, must mention main entities).  
3. Run spaCy NER on article to extract top PERSON/ORG/DATE/NUM tokens → bullet list under "Key facts".  
4. Cache the combined block and include it in the contextual-words Jinja prompt (`{{ context_block }}`).  
5. Extend validator: any entity in Key facts must appear in `original_word` list; reject otherwise.  
6. Unit tests + QA smoke update. 