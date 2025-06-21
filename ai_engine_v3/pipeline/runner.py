from __future__ import annotations
"""End-to-end runner for **AI-Engine v3**.

Key usage patterns:

• Process 5 fresh articles, skip backlog, and serve website:

    OPENROUTER_API_KEY=sk-… python -m ai_engine_v3.pipeline.runner --limit 5 --backfill-limit 0 --serve

• Back-fill at most 20 older articles:

    python -m ai_engine_v3.pipeline.runner --backfill-limit 20
"""
# Ensure API key from config.ini / env is available before any LLM calls
import config.api_config  # noqa: F401

import argparse, logging, pathlib, subprocess, sys, http.server, socketserver, webbrowser

from . import config  # type: ignore
from .scraper import SmartScraper  # duplicated file
from .curator_v2 import CuratorV2
from ..processor import ProcessorV2  # noqa: E402
from ..storage import Storage  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
ROOT = pathlib.Path(__file__).resolve().parent.parent  # ai_engine_v2/


def run_pipeline(limit: int | None = None, backfill_limit: int | None = None):
    logger.info("\n🟢🟢🟢  Better French AI-Engine v3 Run  🟢🟢🟢\n")
    logger.info("📡 Scraping sources …")
    scraper = SmartScraper()
    raw_articles = scraper.comprehensive_scrape()
    logger.info("Fetched %d raw articles", len(raw_articles))

    curator = CuratorV2()
    curated = curator.curate(raw_articles)
    logger.info("🏆 %d articles passed curator", len(curated))

    # Map curator output → Article model objects (minimal fields)
    pending = []
    from ..models import Article, QualityScores  # inline import to avoid heavy deps if not needed

    for art in curated:
        qs = QualityScores(
            quality_score=art.quality_score,
            relevance_score=art.relevance_score,
            importance_score=art.importance_score,
            total_score=art.total_score,
        )
        pending.append(
            Article(
                original_article_title=art.original_data.get("title", ""),
                original_article_link=art.original_data.get("link", ""),
                original_article_published_date=art.original_data.get("published", ""),
                source_name=art.original_data.get("source_name", "unknown"),
                quality_scores=qs,
                original_article_content=art.original_data.get("content", ""),
            )
        )

    # Merge with existing pending queue (keep older items)
    existing_pending = Storage.load_pending()
    all_pending = existing_pending + pending
    Storage.save_pending(all_pending)

    # Process with AI-Engine v2
    logger.info("🤖 Processing with AI-Engine v2 … (titles, summaries, vocab)")
    proc = ProcessorV2()
    proc.batch_process(pending[:limit] if limit else pending)

    # ---------------- Back-fill pass (optional) ----------------
    to_fix = [
        a
        for a in Storage.load_pending()
        if not a.contextual_title_explanations and a.backfill_attempts < 3
    ]

    if backfill_limit is None:
        # Unlimited backlog (default)
        pass
    elif backfill_limit <= 0:
        to_fix = []
    else:
        to_fix = to_fix[:backfill_limit]
    if to_fix:
        logger.info("🔄 Back-filling explanations for %d earlier articles", len(to_fix))
        proc.batch_process(to_fix)

    logger.info("✨ Done – rolling feed updated.")


def serve_ui(port: int = 8010):
    site_dir = ROOT / "website"
    if not site_dir.exists():
        logger.error("website directory not found. Did you copy the site?")
        return
    # Ensure we serve files *from* website even when script is launched from repo root
    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(*args, directory=str(site_dir), **kwargs)
    with socketserver.TCPServer(("", port), handler) as httpd:
        logger.info("🌐 Serving on http://localhost:%d/ (Ctrl+C to quit)", port)
        webbrowser.open(f"http://localhost:{port}")
        httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="Run full AI-Engine v3 pipeline")
    parser.add_argument("--limit", type=int, default=None, help="Max fresh articles to AI-process")
    parser.add_argument(
        "--backfill-limit",
        type=int,
        default=None,
        help="Max backlog articles to AI-process (0 = skip, omit for unlimited)",
    )
    parser.add_argument("--serve", action="store_true", help="Serve website after processing")
    parser.add_argument("--serve-only", action="store_true", help="Only serve website, skip pipeline")
    args = parser.parse_args()

    if args.serve_only:
        serve_ui()
        return

    run_pipeline(args.limit, args.backfill_limit)
    if args.serve:
        serve_ui()


if __name__ == "__main__":
    main() 