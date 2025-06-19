#!/usr/bin/env python3
"""Merge delta raw files into a single JSON stream.
Usage:
  python scripts/raw_merge.py --days 3      # last 3 days
  python scripts/raw_merge.py --day 2025-06-18
Output is printed to stdout as JSON Lines (one article per line).
"""
from __future__ import annotations
import argparse, pathlib, json, sys, datetime, gzip

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw_archive"


def iter_files(days: int | None, day: str | None):
    if day:
        dir_path = RAW_DIR / day
        if dir_path.is_dir():
            yield from sorted(dir_path.glob("*_delta.json"))
    else:
        cutoff = datetime.date.today() - datetime.timedelta(days=days or 1)
        for d in sorted(RAW_DIR.iterdir()):
            if d.is_dir() and d.name >= cutoff.isoformat():
                yield from sorted(d.glob("*_delta.json"))


def main():
    parser = argparse.ArgumentParser(description="Merge raw delta files to stdout (JSON Lines)")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--day", type=str, help="YYYY-MM-DD directory to merge")
    g.add_argument("--days", type=int, help="Merge N most recent days")
    args = parser.parse_args()

    files = list(iter_files(args.days, args.day))
    seen = set()
    for fp in files:
        data = json.loads(fp.read_text())
        for item in data:
            h = item.get("link") or item.get("original_article_link")
            if h and h not in seen:
                seen.add(h)
                sys.stdout.write(json.dumps(item, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main() 