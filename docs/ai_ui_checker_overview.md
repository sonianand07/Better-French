# Better-French Automated Checker Bot

_Last updated: 2025-06-14_

## 0. Why this exists

• Manually refreshing the page and sending screenshots is slow and error-prone.  
• We need the assistant (or any CI job) to *see* the live site, verify design + data, and tell us immediately if something is wrong (e.g. split proper names, missing hover text, layout shifts).  
• This document is the single source of truth for how the automated checker works and how to run / extend it.

---
## 1. What the bot does

1. Builds or fetches the latest `test_articles.json` (via `generate_live_batch.py`).  
2. Starts a **temporary local server** that serves `Project-Better-French-Website/` on a random free port.  
3. Launches a **headless Chromium** session (Playwright) and loads `/`.  
4. Waits for the UI to finish fetching the JSON (checks `window.__BF_LOADED === true`).  
5. Runs a small suite of assertions:
   • No consecutive green word-spans that are both capitalised (proper-name split check).  
   • Switching modes (`learner` ⇄ `native`) toggles hover behaviour correctly.  
   • First 3 article cards expand / collapse summaries.  
   • Page has ≥ N articles; latest date ≥ today-1.  
6. Optionally captures **visual snapshots** (Percy) and **accessibility scan** (Axe).
7. Kills the temp server and prints a summary.  
   • Exit 0 → all good.  
   • Exit 1 → first failing assertion printed to stdout.

---
## 2. Tech stack

| Layer | Tool | Why |
|-------|------|-----|
| Headless browser | **Playwright** | Modern, reliable, TS/JS or Python; easy parallelism |
| Visual diff (opt.) | **Percy** | Pixel-level regression catching subtle design shifts |
| Accessibility (opt.) | **Axe-playwright** | WCAG checks each run |
| Temp server | Python's `http.server` | Zero-config, no extra deps |

---
## 3. Repository layout (proposed)

```
scripts/
  generate_live_batch.py       # already exists – will call ui checker at end
  run_ui_checks.sh             # tiny shell wrapper (spawns server, runs tests)

tests/
  ui_smoke.spec.ts             # Playwright test suite

Makefile                       # convenience targets (see below)
```

---
## 4. Setup (one-time)

```bash
# Install deps
pip install playwright percy-cli axe-playwright
playwright install chromium
```

Inside `Project Better French/` run:
```bash
make live_batch   # runs the AI engine, writes test_articles.json
make ui_test      # launches the checker bot
```
Both targets simply proxy to the scripts + Playwright.

---
## 5. CI integration (optional)

Create a GitHub Actions workflow:
```yaml
on:  pull_request
jobs:
  qa:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: {python-version: '3.11'}
      - run: pip install -r requirements.txt playwright percy-cli axe-playwright
      - run: playwright install chromium --with-deps
      - run: make live_batch OPENROUTER_API_KEY=${{secrets.OPENROUTER_API_KEY}}
      - run: make ui_test
```
Percy diff links automatically appear in the PR if a visual change is detected.

---
## 6. Extending the suite

* **New interactive feature**? Add a Playwright test block and (if visual) a Percy snapshot.  
* **Data rule**? Assert it in `tests/ui_smoke.spec.ts` – e.g. verify each article has `contextual_title_explanations`.

---
## 7. Running locally in one line

```bash
OPENROUTER_API_KEY=sk-xxx make live_batch ui_test
```

If everything passes you'll see:
```
✅ 19/19 articles verified
✅ Visual diff matches baseline
✨ All checks passed in 35 s
```

---
## 8. Troubleshooting

• **Playwright cannot find browser** → run `playwright install chromium`.  
• **Port already in use** → `run_ui_checks.sh` picks a random port; set `$BF_UI_PORT` manually if needed.  
• **Percy token missing** → set `PERCY_TOKEN`; or run with `VISUAL=0` to skip snapshots.

---
## 9. Roadmap ideas

• Add Lighthouse performance budget.  
• Push daily production feed through the same suite and post a Slack summary.  
• Gather hover-tooltip coverage metrics (percent of words with explanations).

---
**Outcome:** With this checker in place, the assistant (and future LLM teammates) can regenerate data, run the suite, and *know* the site is good before pinging you. 