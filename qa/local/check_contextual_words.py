#!/usr/bin/env python3
"""Smoke-test: ensure every live article has contextual words with adequate coverage.

Run locally:
    python qa/local/check_contextual_words.py
    # or point to a specific file / URL
    python qa/local/check_contextual_words.py --path path/to/rolling_articles.json
    python qa/local/check_contextual_words.py --url https://better-french.netlify.app

Exit status is non-zero only when **>20 %** of articles completely lack explanations;
otherwise it prints a report and exits 0 so CI can treat it as warning-only.
"""
from __future__ import annotations

import argparse, json, pathlib, sys, urllib.request, urllib.error
from datetime import datetime
from typing import Iterable

from ai_engine_v3.validator import coverage_ok  # v3 helper

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_PATH = REPO_ROOT / "ai_engine_v3" / "website" / "rolling_articles.json"


# -----------------------------------------------------------------------------
# helpers
# -----------------------------------------------------------------------------


def _parse_iso(ds: str | None):
    if not ds:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(ds[: len(fmt)], fmt)
        except Exception:
            continue
    return None


def _load_articles_from_file(path: pathlib.Path):
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("articles", [])


def _load_articles_from_url(base_url: str):
    import ssl

    json_url = base_url.rstrip("/") + "/rolling_articles.json"
    try:
        with urllib.request.urlopen(json_url, timeout=10) as resp:
            data = json.load(resp)
    except urllib.error.URLError as e:
        # Retry without SSL verification on cert issues (useful for preview sites)
        if isinstance(e.reason, ssl.SSLError):
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(json_url, context=ctx, timeout=10) as resp:
                data = json.load(resp)
            print(f"⚠️  SSL verification skipped for {json_url}")
        else:
            raise
    return data.get("articles", [])


# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------


def main(args: Iterable[str] | None = None):
    parser = argparse.ArgumentParser(description="Check contextual explanations in rolling feed")
    parser.add_argument("--path", type=pathlib.Path, default=DEFAULT_PATH, help="Local rolling_articles.json path")
    parser.add_argument("--url", type=str, help="Base URL of deployed site (script will fetch JSON)")
    ns = parser.parse_args(args)

    try:
        articles = _load_articles_from_url(ns.url) if ns.url else _load_articles_from_file(ns.path)
    except Exception as e:
        print(f"❌ Failed to load articles: {e}")
        sys.exit(1)

    total = len(articles)
    missing = gaps = zero_matches = 0

    for art in articles:
        title = art.get("original_article_title", "")
        ctxt = art.get("contextual_title_explanations") or {}
        if not ctxt:
            missing += 1
            continue

        if not coverage_ok(title, ctxt):
            gaps += 1

        # simple visible-match check (at least one key appears in title, case-insensitive)
        keys = [k.lower() for k in (ctxt.keys() if isinstance(ctxt, dict) else [d.get("original_word", "") for d in ctxt])]
        if not any(k and k in title.lower() for k in keys):
            zero_matches += 1

    ok = total - missing - gaps - zero_matches

    print(f"Total articles: {total}")
    print(f"✓ Good contextual coverage: {ok}")
    print(f"❌ Missing explanations: {missing}")
    print(f"⚠️  Coverage gaps (logic says incomplete): {gaps}")
    print(f"🚫 No visible matches in title: {zero_matches}\n")

    # Fail only if >20 % completely missing
    if missing / max(total, 1) > 0.20:
        print("❌ Too many articles lack contextual explanations – failing CI.")
        sys.exit(2)

    print("✅ Contextual-word smoke test finished (warnings allowed).")


if __name__ == "__main__":
    main() 