#!/usr/bin/env python3
"""Generate a 20-article AI-enhanced sample for local UI testing.
Run: python scripts/generate_sample_batch.py
The file will be written to Project-Better-French-Website/test_articles.json
"""
import json, pathlib, datetime, os
from importlib.util import spec_from_file_location, module_from_spec
# Load local secrets if present
from os import getenv

# Dynamically import AI-Engine (filename has a dash)
ai_engine_path = pathlib.Path(__file__).parent / "AI-Engine.py"
_spec = spec_from_file_location("ai_engine", ai_engine_path)
ai_engine = module_from_spec(_spec)
_spec.loader.exec_module(ai_engine)  # type: ignore
CostOptimizedAIProcessor = ai_engine.CostOptimizedAIProcessor

# Pick a recent curated file
curated_files = sorted((pathlib.Path("data/live").glob("curated_articles_*.json")), reverse=True)
if not curated_files:
    raise SystemExit("No curated_articles_*.json files found in data/live")

latest = curated_files[0]
print(f"📄 Using {latest}")
# Handle both structures 'articles' and 'curated_articles'
raw = json.load(latest.open())
if 'articles' in raw:
    articles = raw['articles'][:10]
elif 'curated_articles' in raw:
    articles = raw['curated_articles'][:10]
else:
    raise SystemExit('No articles array found in chosen file')

# Disable duplicate filtering for local test
proc = CostOptimizedAIProcessor()
proc.ai_config['skip_duplicate_processing'] = False

processed = []
for art in proc.batch_process_articles(articles):
    # Convert explanations list to object keyed by original_word for UI
    if isinstance(art.contextual_title_explanations, list):
        art.contextual_title_explanations = {e['original_word']: {
            'display_format': e.get('display_format',''),
            'explanation': e.get('explanation',''),
            'cultural_note': e.get('cultural_note','')
        } for e in art.contextual_title_explanations}
    processed.append(art)

output_path = pathlib.Path("Project-Better-French-Website/test_articles.json")
proc.save_processed_articles(processed, output_path)

# Ensure key name matches UI expectation
with output_path.open() as f:
    data = json.load(f)
if 'processed_articles' in data:
    data['articles'] = data.pop('processed_articles')
    json.dump(data, output_path.open('w'), ensure_ascii=False, indent=2)

print(f"✅ Saved sample to {output_path}\nRefresh your browser.") 