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