#!/usr/bin/env python3
"""Run AI-Engine v2 on a batch of pending articles.

Example:
  OPENROUTER_API_KEY=sk-... python3 scripts/run_ai_v2.py --limit 2
"""
from __future__ import annotations

import argparse, logging, datetime, os, pathlib
from ai_engine_v2.storage import Storage
from ai_engine_v2.processor import ProcessorV2

# ---------------------------------------------------------------------------
# Configure console + file logging so every run is archived under ./logs/
# ---------------------------------------------------------------------------
ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
LOG_DIR = pathlib.Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
log_path = LOG_DIR / f"ai_run_{ts}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_path, encoding="utf-8"),
    ],
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Process pending articles with AI-Engine v2")
    parser.add_argument("--limit", type=int, default=3, help="Max articles to process")
    args = parser.parse_args()

    pending = Storage.load_pending()
    if not pending:
        logger.info("No pending articles found.")
        return

    batch = pending[: args.limit]
    logger.info("Processing %d/%d pending articles", len(batch), len(pending))

    proc = ProcessorV2()
    proc.batch_process(batch)

    # Remove processed from pending and save
    remaining = pending[args.limit :]
    Storage.save_pending(remaining)
    logger.info("Done. Pending queue length: %d", len(remaining))


if __name__ == "__main__":
    main() 