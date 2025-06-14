#!/usr/bin/env python3
"""Diagnostic: report tokens in each article title that are not wrapped in .french-word spans.
Run:
    python3 qa/tests/check_missing.py [http://localhost:8010]
Outputs a list of titles with missing tokens and suggestions.
"""
from __future__ import annotations
import re, sys, json, urllib.parse
from playwright.sync_api import sync_playwright

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8010"

TOKEN_RE = re.compile(r"\w+[’'\w]*|[:;!?«»,]+|[/-]|\d+|\S", re.UNICODE)

# Helper to detect a word-like token (letters or digits with optional apostrophes)
WORD_RE = re.compile(r"^[\wÀ-ÿ]+(?:[’']?[\wÀ-ÿ]+)*$", re.UNICODE)

def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_function("() => window.__BF_LOADED === true", timeout=15000)

        # load all pages
        try:
            while page.locator("#load-more").is_visible():
                page.locator("#load-more").click()
                page.wait_for_timeout(200)
        except Exception:
            pass

        cards = page.query_selector_all(".article-card")
        missing_report: list[tuple[str, list[str]]] = []

        for card in cards:
            title_el = card.query_selector(".secondary-title")
            if not title_el:
                continue
            text = title_el.inner_text().strip()
            interactive = {el.inner_text().strip() for el in title_el.query_selector_all(".french-word")}
            # Initial rough tokens
            raw_tokens = [tok.strip() for tok in TOKEN_RE.findall(text) if tok.strip()]

            # Merge hyphenated or slash-separated words/dates into single tokens
            tokens: list[str] = []
            i = 0
            while i < len(raw_tokens):
                # Combine WORD - WORD  -> WORD-WORD
                if (
                    i + 2 < len(raw_tokens)
                    and raw_tokens[i + 1] in {"-", "/"}
                    and WORD_RE.match(raw_tokens[i])
                    and WORD_RE.match(raw_tokens[i + 2])
                ):
                    tokens.append(f"{raw_tokens[i]}{raw_tokens[i + 1]}{raw_tokens[i + 2]}")
                    i += 3
                    continue
                # Skip stand-alone hyphen or slash when not merged
                if raw_tokens[i] in {"-", "/"}:
                    i += 1
                    continue
                tokens.append(raw_tokens[i])
                i += 1
            missing = [tok for tok in tokens if tok not in interactive]
            if missing:
                missing_report.append((text, missing))

        browser.close()

        if not missing_report:
            print("🎉 All tokens have contextual spans.")
            return

        print("🚩 Tokens missing context:")
        for title, miss in missing_report:
            print("-", title)
            print("  missing:", ", ".join(miss))

if __name__ == "__main__":
    main() 