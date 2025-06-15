#!/usr/bin/env python3
"""CI helper: verify Netlify deploy is fresh and UI still works.

1. Poll <base_url>/rolling_articles.json until its `updated_at` is
   newer than (now - max_age).
2. If fresh, run the existing Playwright smoke test against <base_url>.

Usage:
    python qa/tests/test_prod_deploy.py https://<site> [--max-age-min 90]

Exit codes:
    0 – all good
    2 – JSON too old / missing after retries
    3 – smoke test failed (propagated)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SMOKE_PATH = REPO_ROOT / "qa/tests/test_smoke.py"


def fetch_updated_at(url: str) -> dt.datetime | None:
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.load(resp)
        ts_raw: str = data["metadata"]["updated_at"]
        ts = dt.datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        return ts
    except (urllib.error.URLError, KeyError, ValueError, json.JSONDecodeError):
        return None


def wait_for_fresh_json(base_url: str, max_age_min: int, timeout_min: int = 10) -> None:
    json_url = f"{base_url.rstrip('/')}/rolling_articles.json"
    deadline = time.monotonic() + timeout_min * 60
    while time.monotonic() < deadline:
        ts = fetch_updated_at(json_url)
        if ts is not None:
            age = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc) - ts
            if age < dt.timedelta(minutes=max_age_min):
                print(f"✅ JSON fresh – age {age}")
                return
            else:
                print(f"ℹ️  JSON age {age} (max {max_age_min}m) – waiting …")
        else:
            print("ℹ️  rolling_articles.json not ready – waiting …")
        time.sleep(30)
    print("❌ Netlify deploy is stale or missing after waiting.")
    sys.exit(2)


def run_smoke(base_url: str) -> None:
    cmd = [sys.executable, str(SMOKE_PATH), base_url]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("❌ Smoke test failed.")
        sys.exit(e.returncode or 3)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    parser.add_argument("--max-age-min", type=int, default=90)
    args = parser.parse_args()

    wait_for_fresh_json(args.base_url, args.max_age_min)
    run_smoke(args.base_url)


if __name__ == "__main__":
    main() 