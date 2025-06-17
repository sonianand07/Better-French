#!/usr/bin/env python3
"""Print titles lacking contextual_title_explanations in rolling_articles.json"""
import json, pathlib, sys
fp = pathlib.Path('Project-Better-French-Website/rolling_articles.json')
data = json.loads(fp.read_text())
missing = []
for i, art in enumerate(data.get('articles', [])):
    ctx = art.get('contextual_title_explanations')
    empty = ctx is None or (isinstance(ctx, dict) and not ctx) or (isinstance(ctx, list) and not ctx)
    if empty:
        missing.append((i + 1, art.get('title') or art.get('original_article_title', '')[:120]))
print(f"Total articles: {len(data.get('articles', []))}")
print(f"Missing contextual explanations: {len(missing)}")
for idx, title in missing:
    print(f"{idx:3}: {title}") 