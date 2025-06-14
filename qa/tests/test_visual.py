#!/usr/bin/env python3
"""Visual regression smoke test.

Takes full-page screenshot and compares against a baseline stored in
`qa/fixtures/baseline_home.png`.

If the baseline does not exist, it will be created automatically and the test
will PASS (acts as first-run setup).  Subsequent runs will fail if the total
pixel difference exceeds 2 %.
"""
from __future__ import annotations
import sys
import pathlib
import numpy as np
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8010"
BASE_DIR = pathlib.Path(__file__).parent.parent
FIXTURE_DIR = BASE_DIR / "fixtures"
FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
BASELINE_PATH = FIXTURE_DIR / "baseline_home.png"
THRESHOLD = 0.02  # 2 % of pixels


def screenshot_png(page) -> bytes:
    # Use full page screenshot with stable viewport
    return page.screenshot(full_page=True)


def diff_images(img1: Image.Image, img2: Image.Image) -> float:
    # Resize to smaller of two to align
    w = min(img1.width, img2.width)
    h = min(img1.height, img2.height)
    img1 = img1.crop((0, 0, w, h))
    img2 = img2.crop((0, 0, w, h))
    diff = ImageChops.difference(img1, img2).convert("L")
    arr = np.array(diff)
    # count non-zero pixels
    diff_pixels = np.count_nonzero(arr > 10)  # tolerance
    total = arr.size
    return diff_pixels / total


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_function("() => window.__BF_LOADED === true", timeout=15000)

        # Ensure all articles loaded via pagination before taking screenshot
        try:
            while page.locator("#load-more").is_visible():
                page.locator("#load-more").click()
                page.wait_for_timeout(200)
        except Exception:
            pass

        png_bytes = screenshot_png(page)
        browser.close()

    current_img = Image.open(io.BytesIO(png_bytes))

    if not BASELINE_PATH.exists():
        current_img.save(BASELINE_PATH)
        print("ℹ️ Baseline screenshot created (first run) – test passes by default.")
        sys.exit(0)

    baseline_img = Image.open(BASELINE_PATH)
    diff_ratio = diff_images(baseline_img, current_img)

    if diff_ratio > THRESHOLD:
        print(f"❌ Visual diff failed – {diff_ratio*100:.2f}% of pixels differ (threshold {THRESHOLD*100:.1f}%).")
        # save current for manual inspection
        current_img.save(FIXTURE_DIR / "current_home.png")
        sys.exit(1)
    else:
        print("✅ Visual diff passed (difference {:.2f}%).".format(diff_ratio*100))
        sys.exit(0)


if __name__ == "__main__":
    import io
    main() 