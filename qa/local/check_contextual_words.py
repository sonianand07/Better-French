#!/usr/bin/env python3
"""Quick smoke-test: ensure every live article has contextual words and good coverage.

Usage:  python qa/local/check_contextual_words.py [--path path/to/rolling_articles.json]
Outputs a short report and exits with non-zero status if more than 20 % of
the items are missing contextual data, so CI can fail.
"""
from __future__ import annotations

import argparse, json, pathlib, sys, urllib.request, urllib.error
from datetime import datetime

# Reuse validator helper for coverage measure
from ai_engine_v2.validator import coverage_ok

DEFAULT_PATH = (
    pathlib.Path(__file__).resolve().parent.parent.parent  # repo root
    / "Project-Better-French-Website"
    / "rolling_articles.json"
)


def main():
    parser = argparse.ArgumentParser(description="Check contextual explanations in rolling feed")
    parser.add_argument("--path", type=pathlib.Path, default=DEFAULT_PATH, help="Local rolling_articles.json path")
    parser.add_argument("--url", type=str, help="Base URL of deployed site (script will fetch /rolling_articles.json)")
    args = parser.parse_args()

    # Load JSON from URL or path
    if args.url:
        json_url = args.url.rstrip("/") + "/rolling_articles.json"
        import ssl
        try:
            with urllib.request.urlopen(json_url, timeout=10) as resp:
                data = json.load(resp)
        except urllib.error.URLError as e:
            # Retry without SSL verification if the first failure was due to certificate
            if isinstance(e.reason, ssl.SSLError):
                try:
                    ctx = ssl._create_unverified_context()
                    with urllib.request.urlopen(json_url, context=ctx, timeout=10) as resp:
                        data = json.load(resp)
                    print(f"⚠️  SSL verification skipped for {json_url}")
                except Exception as e2:
                    print(f"❌ Failed to fetch {json_url}: {e2}")
                    sys.exit(1)
            else:
                print(f"❌ Failed to fetch {json_url}: {e}")
                sys.exit(1)
        except ValueError as e:
            print(f"❌ Failed to decode JSON from {json_url}: {e}")
            sys.exit(1)
    else:
        if not args.path.exists():
            print(f"❌ File not found: {args.path}")
            sys.exit(1)
        data = json.loads(args.path.read_text(encoding="utf-8"))

    articles = data.get("articles", [])
    total = len(articles)
    missing = 0          # no explanations dict at all
    zero_matches = 0     # explanations exist but NONE of the keys appear in title (what user sees)
    gaps = 0             # coverage_ok failed (some matches but insufficient)
    bad_heading = 0
    ordering_issue = False

    # Helper to parse ISO or RFC dates roughly
    def _parse_date(ds: str | None):
        if not ds:
            return None
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%a, %d %b %Y %H:%M:%S", "%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(ds[:len(fmt)], fmt)
            except Exception:
                continue
        return None

    for art in articles:
        ctxt = art.get("contextual_title_explanations") or {}
        if not ctxt:
            missing += 1
            continue

        title = art.get("original_article_title", "")

        # VISUAL MATCH: does at least one explanation key appear verbatim in the title?
        # Normalize common punctuation variants so "Iran/Israël" ~ "Iran-Israël"
        norm_title = (
            title.replace("/", "-")
            .replace("\u2019", "'")  # curly apostrophe to straight
            .lower()
        )

        keys = [k.replace("/", "-").replace("\u2019", "'").lower() for k in ctxt.keys()]
        found_any = any(k in norm_title for k in keys if k and len(k) > 1)

        if not found_any:
            zero_matches += 1

        if not coverage_ok(title, ctxt):
            gaps += 1

        # ---------- new heading quality check ----------
        def _heading_is_french(display_fmt: str, original: str) -> bool:
            import re
            m = re.match(r"\*\*([^:]+):", display_fmt or "")
            if not m:
                return True
            heading = m.group(1).strip()
            # accented letter or identical to original token
            return heading.lower() == original.lower() or bool(re.search(r"[À-ÿ]", heading))

        # Iterate list or dict uniformly
        items = ctxt.values() if isinstance(ctxt, dict) else ctxt
        for item in items:
            if not isinstance(item, dict):
                continue
            if _heading_is_french(item.get("display_format", ""), item.get("original_word", "")):
                bad_heading += 1
                break  # one bad per article is enough

    # -------- Ordering check --------
    dates = [
        _parse_date(
            art.get("original_article_published_date")
            or art.get("published")
            or art.get("published_date")
        )
        for art in articles
    ]
    # Keep only non-None
    dates = [d for d in dates if d is not None]
    if any(later < earlier for earlier, later in zip(dates, dates[1:])):
        ordering_issue = True

    ok = total - missing - gaps - zero_matches

    print(f"Total articles: {total}")
    print(f"✓ Good contextual coverage: {ok}")
    print(f"⚠️  Coverage gaps (machine logic says incomplete): {gaps}")
    print(f"🚫 No visible matches in title: {zero_matches}")
    print(f"❌ Missing explanations: {missing}")
    print(f"📑 Ordering OK (newest→oldest): {'YES' if not ordering_issue else 'NO'}")
    print(f"❌ Tooltips with French headings: {bad_heading}")

    if bad_heading or missing / max(total, 1) > 0.20:
        print("❌ Too many articles lack contextual explanations – failing CI.")
        sys.exit(2)


if __name__ == "__main__":
    main() 