#!/usr/bin/env python3
"""Fetch live news (up to 20 articles), process with the new AI engine, and
save to Project-Better-French-Website/test_articles.json so the local UI can
immediately display the results.

Usage:
    python scripts/generate_live_batch.py

Prerequisites:
    • Internet access (to fetch RSS feeds)
    • OPENROUTER_API_KEY exported (for AI processing)
"""
from __future__ import annotations
import json
import pathlib
import datetime
import sys

# --- Dynamic imports to avoid path issues ---------------------------------
from importlib.util import spec_from_file_location, module_from_spec

base_dir = pathlib.Path(__file__).resolve().parent

# Import SmartScraper (standard filename)
smart_scraper_path = base_dir / "smart_scraper.py"
_spec_scraper = spec_from_file_location("smart_scraper", smart_scraper_path)
smart_scraper = module_from_spec(_spec_scraper)
_spec_scraper.loader.exec_module(smart_scraper)  # type: ignore
SmartScraper = smart_scraper.SmartScraper

# Import AI Engine (filename with dash)
ai_engine_path = base_dir / "AI-Engine.py"
_spec_ai = spec_from_file_location("ai_engine", ai_engine_path)
ai_engine = module_from_spec(_spec_ai)
_spec_ai.loader.exec_module(ai_engine)  # type: ignore
CostOptimizedAIProcessor = ai_engine.CostOptimizedAIProcessor

# --- Step 1: Scrape --------------------------------------------------------
print("🔄 Scraping live feeds (this may take ~10-20 s)…", flush=True)
scraper = SmartScraper()
try:
    raw_articles = scraper.comprehensive_scrape()[:20]  # take top 20
except Exception as e:
    sys.exit(f"❌ Scraping failed: {e}")

if not raw_articles:
    sys.exit("❌ Scraper returned 0 articles – aborting.")
print(f"📰 Got {len(raw_articles)} fresh articles.")

# Convert to minimal dicts AI Engine expects (title, summary, link, etc.)
articles_for_ai: list[dict] = []
for a in raw_articles:
    articles_for_ai.append({
        "title": a.title,
        "summary": a.summary or "",
        "link": a.link,
        "published": a.published,
        "source_name": a.source_name,
    })

# --- Step 2: AI processing -------------------------------------------------
print("🤖 Processing with AI engine…", flush=True)
ai_proc = CostOptimizedAIProcessor()
ai_proc.ai_config['skip_duplicate_processing'] = False  # process everything

processed = []
for art in ai_proc.batch_process_articles(articles_for_ai):
    # Turn explanation list → object keyed by word (UI convenience)
    if isinstance(art.contextual_title_explanations, list):
        art.contextual_title_explanations = {
            e['original_word']: {
                'display_format': e.get('display_format', ''),
                'explanation': e.get('explanation', ''),
                'cultural_note': e.get('cultural_note', '')
            } for e in art.contextual_title_explanations
        }
    processed.append(art)
print(f"✅ AI processed {len(processed)} articles.")

# --- Step 3: Save for website ---------------------------------------------
output_path = pathlib.Path("Project-Better-French-Website/test_articles.json")
ai_proc.save_processed_articles(processed, output_path)

# Ensure key name is 'articles'
with output_path.open() as f:
    data = json.load(f)
if 'processed_articles' in data:
    data['articles'] = data.pop('processed_articles')
    json.dump(data, output_path.open('w'), ensure_ascii=False, indent=2)

print(f"💾 Saved to {output_path}")
print("↻ Refresh the browser tab to view the new batch.") 