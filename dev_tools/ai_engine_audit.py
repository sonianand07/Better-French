#!/usr/bin/env python3
"""AI-Engine Baseline Audit (AIE-01)

Collects metrics from AI-Engine logs and recent GitHub-Action run artifacts.
Run locally:  python3 dev_tools/ai_engine_audit.py --days 7
Outputs JSON + Markdown summary in reports/.
"""

import argparse, json, os, re, sys, datetime, pathlib, gzip, logging
from collections import Counter, defaultdict
from typing import List, Dict, Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOGS_DIR = ROOT / 'logs'
REPORTS_DIR = ROOT / 'reports'
REPORTS_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format='[audit] %(message)s')

# Regex patterns for key log lines produced by AI-Engine
RX_ARTICLE_SUCCESS = re.compile(r"✨ AI processed:")
RX_ARTICLE_FAIL = re.compile(r"❌ AI (?:title\+summary|explanation|.*) failed")
RX_RETRY = re.compile(r"⚠️ [\w ]+ word-count .* out of range – will retry")
RX_VALIDATION_MISSING = re.compile(r"missing tokens \[.*\]")


def scan_logs(days: int = 7) -> Dict[str, Any]:
    since = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    metrics = Counter()
    failures: List[str] = []

    for log_file in LOGS_DIR.glob('**/*.log'):
        mtime = datetime.datetime.utcfromtimestamp(log_file.stat().st_mtime)
        if mtime < since:
            continue
        open_fn = gzip.open if log_file.suffix == '.gz' else open
        try:
            with open_fn(log_file, 'rt', encoding='utf-8', errors='ignore') as fh:
                for line in fh:
                    if RX_ARTICLE_SUCCESS.search(line):
                        metrics['success'] += 1
                    elif RX_ARTICLE_FAIL.search(line):
                        metrics['fail'] += 1
                    elif RX_RETRY.search(line):
                        metrics['retry'] += 1
                    elif RX_VALIDATION_MISSING.search(line):
                        metrics['validation_missing'] += 1
        except Exception as e:
            logging.warning(f"Could not read {log_file}: {e}")

    return dict(metrics)


def save_reports(metrics: Dict[str, Any]):
    ts = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    json_path = REPORTS_DIR / f'ai_engine_audit_{ts}.json'
    md_path = REPORTS_DIR / f'ai_engine_audit_{ts}.md'

    with open(json_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logging.info(f"Saved JSON metrics to {json_path}")

    # Simple markdown summary
    total = metrics.get('success', 0) + metrics.get('fail', 0)
    md = [
        f"# AI-Engine Baseline Audit ({ts})\n",
        f"*Articles processed (detected):* **{total}**",  # noqa
        f"*Success:* {metrics.get('success', 0)}",
        f"*Failures:* {metrics.get('fail', 0)}",
        f"*Retries:* {metrics.get('retry', 0)}",
        f"*Validation misses:* {metrics.get('validation_missing', 0)}"
    ]
    with open(md_path, 'w') as f:
        f.write('\n'.join(md))
    logging.info(f"Saved Markdown report to {md_path}")


def main():
    parser = argparse.ArgumentParser(description='AI-Engine baseline audit')
    parser.add_argument('--days', type=int, default=7, help='Look-back period')
    args = parser.parse_args()

    metrics = scan_logs(args.days)
    save_reports(metrics)


if __name__ == '__main__':
    main() 