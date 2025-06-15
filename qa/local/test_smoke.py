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
import json
import urllib.parse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8010"

CAP_RE = re.compile(r"^[A-ZÉÈËÊÀÂÎÏÔÙÛÇ].*")

PUNCT_ONLY_RE = re.compile(r"^[^\w\u00C0-\u017F]+$", re.UNICODE)


def main() -> None:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
            # Wait for our global loaded flag (set in script.js after first render)
            page.wait_for_function("() => window.__BF_LOADED === true", timeout=30_000)

            # --- ensure pagination is exhausted ---------------------------
            # Click the "Load more" button repeatedly until it disappears
            try:
                while page.locator("#load-more").is_visible():
                    page.locator("#load-more").click()
                    # Give the DOM a brief moment to append cards
                    page.wait_for_timeout(200)
            except Exception:
                # If the locator becomes detached mid-loop, restart check once
                pass

            # --- basic presence checks --------------------------------------
            article_count = page.locator(".article-card, #featured-article").count()
            if article_count == 0:
                print("❌ No articles found on the page")
                sys.exit(2)

            word_spans = page.locator(".french-word")
            if word_spans.count() == 0:
                print("❌ No interactive word spans found (class .french-word)")
                sys.exit(3)

            # --- tooltip interaction check (Step 5) ------------------------
            # Hover the first interactive word and expect it (and its parent
            # title) to gain the active classes set by the JS.
            first_word = word_spans.nth(0)
            first_word.hover()
            page.wait_for_timeout(100)  # allow DOM to update

            if not first_word.evaluate("e => e.classList.contains('active')"):
                print("❌ Hovering a french-word did not add the 'active' class")
                sys.exit(5)

            parent_title_has_flag = first_word.evaluate("e => e.closest('.secondary-title').classList.contains('has-active-word')")
            if not parent_title_has_flag:
                print("❌ Parent title missing 'has-active-word' after hover")
                sys.exit(6)

            # Clear state with mouse move to body
            page.mouse.move(0, 0)

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

            # ----------------------------------------------------------------
            # Diagnostic: count punctuation-only tokens and duplicates
            # ----------------------------------------------------------------
            token_counts = {}
            punct_counts = {}

            for el in spans:
                # Try to pull the original_word from data-word attribute first
                data_attr = el.get_attribute("data-word")
                original_word = None
                if data_attr:
                    try:
                        decoded = json.loads(urllib.parse.unquote(data_attr))
                        original_word = decoded.get("original_word") or decoded.get("word")
                    except Exception:
                        pass
                if not original_word:
                    original_word = el.inner_text().strip()

                original_word = original_word.strip()
                if not original_word:
                    continue

                token_counts[original_word] = token_counts.get(original_word, 0) + 1
                if PUNCT_ONLY_RE.fullmatch(original_word):
                    punct_counts[original_word] = punct_counts.get(original_word, 0) + 1

            total_punct = sum(punct_counts.values())
            if total_punct:
                print(f"ℹ️  Punctuation-only tokens: {total_punct} across {len(punct_counts)} distinct symbols → {punct_counts}")
            else:
                print("👍 No punctuation-only tokens detected.")

            duplicate_tokens = {t: c for t, c in token_counts.items() if c > 1}
            if duplicate_tokens:
                top_dupes = ", ".join(f"{tok}({cnt})" for tok, cnt in sorted(duplicate_tokens.items(), key=lambda it: it[1], reverse=True)[:10])
                print(f"ℹ️  Tokens appearing more than once: {len(duplicate_tokens)} – Top: {top_dupes}")

            browser.close()
    except PlaywrightTimeout:
        print("❌ Timed out waiting for page to load (__BF_LOADED flag). Is the dev server running?")
        sys.exit(5)


if __name__ == "__main__":
    main() 