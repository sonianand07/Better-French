# Future Features Backlog

A central, living list of ideas **not yet implemented** for AI-Engine v3 and the Better-French site.  When a feature ships, move it to the _Done_ section or delete it.

| ID | Feature | Brief | Status |
|----|---------|-------|--------|
| F-001 | **MCP server v2** | Real Modal-Context Protocol service that fetches the live Netlify `rolling_articles.json`, analyses health (article count, stale data, missing fields) and exposes `/status`, `/advice`, `/chat` endpoints for the front-end. | ❌ Pending |
| F-002 | One-click feedback loop | Web tooltip editor + `manual_overrides.json`; pipeline injects fixes into prompts and post-processing. | ❌ Pending |
| F-003 | Playwright UI checker bot | Headless tests + Percy snapshots on every PR. | ❌ Pending |
| F-004 | Supabase raw archive | Upload hourly raw deltas to a bucket; keep only 30 days locally. | ❌ Pending |
| F-005 | Audio TTS (ElevenLabs) | Generate MP3 for each article, add `audio_url` field, play-button on site. | ❌ Pending |
| F-006 | Personalised ranking | Use `personaliser.py` to serve user-specific order based on profile JSON. | ❌ Pending |
| F-007 | UI filters | Difficulty dropdown, tone chips, topic tags. | ❌ Pending |
| F-008 | Backup pruning | Keep last 200 `rolling_*.json` backups, delete older. | ❌ Pending |
| F-009 | Lighthouse perf budget | Automated performance budgets in CI. | ❌ Pending |

## Done

| Feature | Commit / PR |
|---------|-------------|
| Raw-archive moved inside `ai_engine_v3/data/` | a6d5c00 |
| Pre-commit hook enforced in CI | 4084071 |

### Detailed briefs

#### F-001 MCP server v2 – live site health & advice
Rebuild of the discarded FastAPI app.
1. Fetch `https://better-french.netlify.app/rolling_articles.json` or preview URL.
2. Run health checks (article count, schema, missing vocab).
3. Expose `/status`, `/advice`, `/chat` endpoints.
4. Dockerised; optional Supabase function.

#### F-002 One-click feedback loop for tool-tips
Editor fixes stored in `config/manual_overrides.json`.
Workflow: UI ✏️ → POST override → file saved → processor injects & overwrites output.

#### F-003 Playwright UI checker bot
Headless Chromium + Percy + Axe. Runs on PR; fails on regression.

#### F-004 Supabase raw archive storage
Upload hourly raw deltas; keep 30-day local cache only.

#### F-005 Audio TTS (ElevenLabs)
Generate French MP3 per article, save URL, play button on site.

#### F-006 Personalised ranking
`personaliser.py` via FastAPI endpoint, profiles table in Supabase.

#### F-007 UI filters
Difficulty dropdown, tone chips, keyword tags – client side.

#### F-008 Backup pruning
Keep last 200 JSON backups, delete older in workflow.

#### F-009 Lighthouse performance budget
Run `treosh/lighthouse-ci-action` in CI, budget json under `qa/`. 