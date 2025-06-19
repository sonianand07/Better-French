#!/usr/bin/env python3
"""Move selected live articles back to the *pending* queue so they will be
re-processed on the next AI-Engine v2 run.

Usage examples
--------------
# Move the first two (newest) articles back
python scripts/move_to_pending.py --count 2

# Move every article whose title contains "Iran-Israël"
python scripts/move_to_pending.py --title "Iran-Israël"
"""
from __future__ import annotations

import argparse, json, pathlib, sys
from typing import List, Dict, Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
ROLLING_FILE = ROOT / "Project-Better-French-Website" / "rolling_articles.json"
PENDING_FILE = ROOT / "ai_engine_v2" / "data" / "live" / "pending_articles.json"


def _load(path: pathlib.Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("articles", data)


def _save(path: pathlib.Path, articles: List[Dict[str, Any]]):
    path.write_text(json.dumps({"articles": articles}, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description="Move live articles back to pending queue")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--count", type=int, help="Move N newest articles")
    grp.add_argument("--title", help="Move articles whose title contains this substring (case-insensitive)")
    args = ap.parse_args()

    rolling = _load(ROLLING_FILE)
    if not rolling:
        print("🚫 rolling_articles.json is empty – nothing to do.")
        return

    pending = _load(PENDING_FILE)

    if args.count:
        to_move, keep = rolling[: args.count], rolling[args.count :]
    else:
        to_move, keep = [], []
        match = args.title.lower()
        for art in rolling:
            if match in art.get("original_article_title", "").lower():
                to_move.append(art)
            else:
                keep.append(art)

    if not to_move:
        print("⚠️  No articles matched your criteria.")
        return

    # reset back-fill counter so they are eligible for up to 3 fresh retries
    for art in to_move:
        art["backfill_attempts"] = 0

    # prepend moved articles to pending list so they're processed first
    _save(PENDING_FILE, to_move + pending)
    _save(ROLLING_FILE, keep)

    print(f"🌀 Moved {len(to_move)} article(s) back to pending. Pending queue is now {len(to_move) + len(pending)} items.")


if __name__ == "__main__":
    main() 