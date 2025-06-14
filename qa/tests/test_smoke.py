#!/usr/bin/env python3
"""Minimal Playwright smoke-test for Better-French UI.

Usage:
    python qa/tests/test_smoke.py [http://localhost:8010]

The script loads the given URL (defaults to the local dev server), waits for
`window.__BF_LOADED` to become true, then performs three basic checks:

1. The page contains at least one article card.
2. There are interactive `.french-word` spans (hoverable words).
3. No consecutive capitalised words with the **same** explanation are rendered
   as separate spans – a quick proxy for the "Donald Trump" split-name bug.

Exit code 0  = pass.
Exit code 1+ = failure (message printed).
"""
from __future__ import annotations
import sys
import re

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8010"

CAP_RE = re.compile(r"^[A-ZÉÈËÊÀÂÎÏÔÙÛÇ].*")


def main() -> None:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15_000)
            # Wait for our global loaded flag (set in script.js after first render)
            page.wait_for_function("() => window.__BF_LOADED === true", timeout=15_000)

            # --- basic presence checks --------------------------------------
            article_count = page.locator(".article-card, #featured-article").count()
            if article_count == 0:
                print("❌ No articles found on the page")
                sys.exit(2)

            word_spans = page.locator(".french-word")
            if word_spans.count() == 0:
                print("❌ No interactive word spans found (class .french-word)")
                sys.exit(3)

            # --- split-name heuristic --------------------------------------
            # Iterate over secondary title spans in DOM order
            spans = word_spans.element_handles()
            for i in range(len(spans) - 1):
                s1, s2 = spans[i], spans[i + 1]
                t1 = s1.inner_text().strip()
                t2 = s2.inner_text().strip()

                if CAP_RE.match(t1) and CAP_RE.match(t2):
                    data1 = s1.get_attribute("data-word")
                    data2 = s2.get_attribute("data-word")
                    if data1 and data1 == data2:
                        print("❌ Detected split proper name:", t1, t2)
                        sys.exit(4)

            print("✅ Smoke test passed (articles loaded, interactive words present, no split names detected).")
            browser.close()
    except PlaywrightTimeout:
        print("❌ Timed out waiting for page to load (__BF_LOADED flag). Is the dev server running?")
        sys.exit(5)


if __name__ == "__main__":
    main() 