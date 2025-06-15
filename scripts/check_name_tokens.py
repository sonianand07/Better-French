#!/usr/bin/env python3
"""Check that multi-word proper names in titles appear as a single key in contextual_title_explanations.

Usage:  python scripts/check_name_tokens.py  [N]
If N is given, only the first N articles in rolling_articles.json are checked (default 20).

The script prints a table showing whether each article passes the name-merging rule.
"""
from __future__ import annotations

import json, pathlib, re, sys
from typing import List

ROLLING_PATH = pathlib.Path('Project-Better-French-Website/rolling_articles.json')
MAX_CHECK = int(sys.argv[1]) if len(sys.argv) > 1 else 20

# ---------------------------------------------------------------------------
# Helper: same heuristic as _merge_proper_nouns (condensed)
# ---------------------------------------------------------------------------

def merge_names(text: str) -> List[str]:
    tok = text.split()
    out: List[str] = []
    i = 0
    def cap(tok: str) -> bool:
        t = tok.rstrip('.,:;!?')
        return t and t[0].isupper() and all(c.isalpha() or c in "-.'’" for c in t)

    while i < len(tok):
        run: List[str] = []
        while i < len(tok) and cap(tok[i]):
            run.append(tok[i].rstrip('.,:;!?'))
            i += 1
            if len(run) == 5:
                break
        if len(run) >= 2:
            out.append(" ".join(run))
        elif run:
            out.extend(run)
        else:
            i += 1
    return out

# ---------------------------------------------------------------------------

if not ROLLING_PATH.exists():
    sys.exit(f"❌ {ROLLING_PATH} not found")

data = json.loads(ROLLING_PATH.read_text())
articles = data.get('articles', [])[:MAX_CHECK]

print(f"Checking first {len(articles)} articles in rolling_articles.json\n")
print("Idx | Name tokens merged? | Title snippet")
print("----|---------------------|------------------------------")

fails = 0
for idx, art in enumerate(articles, 1):
    title = art.get('title') or art.get('original_article_title', '')
    expected_names = merge_names(title)
    ctxt = art.get('contextual_title_explanations') or {}
    if isinstance(ctxt, dict):
        keys = set(ctxt.keys())
    elif isinstance(ctxt, list):
        keys = {d.get('original_word') for d in ctxt if isinstance(d, dict)}
    else:
        keys = set()
    # Pass if each expected multi-word name is present exactly as one key
    ok = all(n in keys for n in expected_names if ' ' in n)
    status = '✅' if ok else '❌'
    if not ok:
        fails += 1
    print(f"{idx:>3} | {status:^19} | {title[:50]}")

print(f"\nResult: {fails} / {len(articles)} articles have split name tokens.")

# PATCH_TEST_COMMENT 