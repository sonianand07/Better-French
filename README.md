# Better French Max  
**Automated French-news learning platform** 

[![Netlify Status](https://api.netlify.com/api/v1/badges/undefined/deploy-status)](https://app.netlify.com/sites/ephemeral-florentine-48f9c7/deploys)

Live demo ➜ https://ephemeral-florentine-48f9c7.netlify.app

---

## ✨ What is it?
Better French Max scrapes the French press, filters for high-quality / expat-relevant articles, enriches them with AI-generated summaries & vocabulary help, then publishes the result to a minimalist bilingual website.

*Read the news & learn French at the same time – automatically.*

---

## 🗂️ Repo layout (top level)
```
.
├─ scripts/                  # Scraper, curator, AI processor, scheduler, updater
├─ config/                  # Central settings & API keys
├─ Project-Better-French-Website/  # Static site (HTML/CSS/JS)
├─ data/                    # Live JSON output written by the pipeline
├─ logs/                    # Runtime & debug logs
├─ automation_controller.py # One-shot orchestrator (run the full pipeline)
└─ Dockerfile / requirements.txt
```

> The website itself has its own `README.md` inside the `Project-Better-French-Website/` folder with UI details.

---

## 🚀 Quick start (local)
```bash
# 1. Clone & enter
$ git clone https://github.com/<your-username>/Better-French.git
$ cd Better-French

# 2. Create a virtualenv & install deps
$ python3 -m venv venv && source venv/bin/activate
$ pip install -r requirements.txt

# 3. Provide your OpenRouter API key for AI processing
$ export OPENROUTER_API_KEY="sk-..."  # or edit config/api_config.py

# 4. Run the pipeline once (regular update)
$ python automation_controller.py --regular

# 5. Serve the static site (for local preview)
$ cd Project-Better-French-Website
$ python3 -m http.server 8000
# → open http://localhost:8000
```

No API key? The pipeline will still scrape & curate, it just skips the AI-enhancement step.

---

## 🔧 Automation / Production
* **Scheduler**: `scripts/run_scheduler.sh` runs both breaking-news (every 30 min) and regular (every 2 h) jobs via `scheduler_main.py`.
* **Deploy**: the main branch is wired to Netlify; pushing commits triggers a rebuild. Static assets are served from `Project-Better-French-Website/`.
* **Data path in prod**: JSON is written to `data/live/current_articles.json` and picked up by the front-end's `script.js`.

---

## 🏗️ High-level architecture
```
SmartScraper → QualityCurator → CostOptimizedAIProcessor → LiveWebsiteUpdater → Static Site (Netlify)
```
* Central config lives in `config/automation.py` (cost limits, quality thresholds, scheduling, etc.).
* All modules log to both console and `logs/*.log`.

---

## 📑 Environment variables
| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | Required for AI text generation |
| `TZ` | (Optional) timezone for logs & cron |

---

## 🤝 Contributing
1. Fork / branch from `main`.
2. Make changes (include tests or a demo run if relevant).
3. Open a pull request – please describe *why* and *how*.

---

## 🪪 License
This project is MIT-licensed (see `LICENSE`). 