#!/usr/bin/env python3
"""Fetch raw news articles on a frequent schedule (e.g. every 30 min).
Saves to ai_engine_v3/data/raw_archive/raw_scrape_<timestamp>.json
"""
from __future__ import annotations

import datetime, pathlib, json, logging, argparse, hashlib, json
from ai_engine_v3.pipeline.scraper import SmartScraper
import shutil

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # repo root
RAW_DIR = ROOT / "data" / "raw_archive"
RAW_DIR.mkdir(parents=True, exist_ok=True)

VISITED_PATH = ROOT / "ai_engine_v3" / "data" / "_cache" / "visited_hashes.json"
VISITED_PATH.parent.mkdir(parents=True, exist_ok=True)

def _link_hash(link: str) -> str:
    return hashlib.sha1(link.encode("utf-8")).hexdigest()

def _load_visited() -> set[str]:
    if not VISITED_PATH.exists():
        return set()
    try:
        return set(json.loads(VISITED_PATH.read_text()))
    except Exception:
        return set()

def _save_visited(s: set[str]):
    tmp = VISITED_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(list(s)))
    tmp.replace(VISITED_PATH)

def main():
    parser = argparse.ArgumentParser(description="Fetch raw news articles.")
    parser.add_argument("--hours-back", type=int, default=6, help="Keep only items published in last N hours (default 6)")
    args = parser.parse_args()

    now = datetime.datetime.utcnow()
    ts = now.strftime("%Y%m%d_%H%M%S")

    scraper = SmartScraper()
    raw_all = scraper.comprehensive_scrape()

    # optional time filter
    if args.hours_back:
        from dateutil import parser as dt_parser
        import datetime as dt
        cutoff = dt.datetime.utcnow() - dt.timedelta(hours=args.hours_back)

        def _to_utc_naive(ds):
            try:
                dt_obj = dt_parser.parse(ds)
                if dt_obj.tzinfo:
                    dt_obj = dt_obj.astimezone(dt.timezone.utc).replace(tzinfo=None)
                return dt_obj
            except Exception:
                return cutoff - dt.timedelta(days=1)  # ensure filter drops bad dates

        raw_filtered = [a for a in raw_all if (_to_utc_naive(a.published) if a.published else cutoff) >= cutoff]
    else:
        raw_filtered = raw_all

    # ---------------- Delta dedup ----------------
    visited = _load_visited()
    new_items = []
    for art in raw_filtered:
        h = _link_hash(art.link or art.original_data.get("link", ""))
        if h and h not in visited:
            visited.add(h)
            new_items.append(art)

    if not new_items:
        logger.info("No new unique articles in this fetch window.")
        return

    # write delta file under dated directory
    day_dir = RAW_DIR / now.strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    out_path = day_dir / f"{ts}_delta.json"
    articles_payload = [a.__dict__ for a in new_items]

    json.dump(articles_payload, out_path.open("w", encoding="utf-8"), ensure_ascii=False)
    _save_visited(visited)

    # rotation: keep last 90 days directories
    dirs = sorted(p for p in RAW_DIR.iterdir() if p.is_dir())
    if len(dirs) > 90:
        for d in dirs[:-90]:
            shutil.rmtree(d, ignore_errors=True)

    logger.info("Fetched %d new unique articles -> %s", len(new_items), out_path)

if __name__ == "__main__":
    main() 