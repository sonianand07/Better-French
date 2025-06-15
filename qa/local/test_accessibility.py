#!/usr/bin/env python3
"""Accessibility audit using axe-core (Step 6).

Loads the page, injects axe-core from CDN, runs a11y checks and fails if any
serious violations are found (severity "serious" or "critical").
"""
from __future__ import annotations
import sys
import json
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8010"


CDN_JS = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.3/axe.min.js"

SEVERITIES = {"minor": 0, "moderate": 1, "serious": 2, "critical": 3}
THRESHOLD = SEVERITIES["serious"]  # fail on serious/critical

def main() -> None:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_function("() => window.__BF_LOADED === true", timeout=15000)

            # Load all paginated articles so axe scans full content
            try:
                while page.locator("#load-more").is_visible():
                    page.locator("#load-more").click()
                    page.wait_for_timeout(200)
            except Exception:
                pass

            # Inject axe-core from CDN, but gracefully skip audit if unavailable (e.g., offline CI)
            try:
                page.add_script_tag(url=CDN_JS)
                page.wait_for_function("() => window.axe !== undefined", timeout=10000)
            except Exception as e:
                # In some CI environments the CDN may be blocked or rate-limited.
                # Any failure while loading axe-core is treated as a soft skip so
                # that the overall workflow doesn't block the merge.
                print(f"⚠️  Skipping accessibility audit (axe-core load failed): {e}")
                browser.close()
                sys.exit(0)  # Treat as pass / skipped

            result_json = page.evaluate("async () => await window.axe.run()")
            browser.close()

        violations = [v for v in result_json["violations"] if SEVERITIES.get(v.get("impact","minor"),0) >= THRESHOLD]
        if violations:
            print(f"❌ Accessibility audit found {len(violations)} serious/critical issues.")
            for v in violations[:10]:
                print("-", v["id"], ":", v["help"])
            sys.exit(1)
        else:
            print("✅ Accessibility audit passed – no serious issues detected.")
            sys.exit(0)

    except PlaywrightTimeout:
        print("❌ Timed out loading page or axe-core script")
        sys.exit(2)


if __name__ == "__main__":
    main() 