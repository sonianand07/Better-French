#!/usr/bin/env python3
"""Quick test pipeline – processes a handful of fresh articles with the new context-block prompts.

Safe to run locally; does NOT touch pending/backfill storage and does not start the website.
Usage (from repo root):
    OPENROUTER_API_KEY=sk-... python3 -m ai_engine_v3.scripts.quick_test_pipeline --limit 5
"""
from __future__ import annotations

import argparse, logging, sys

# Ensure API key is loaded from config.ini or env
import config.api_config  # noqa: F401

from ai_engine_v3.pipeline.scraper import SmartScraper
from ai_engine_v3.pipeline.curator_v2 import CuratorV2
from ai_engine_v3.processor import ProcessorV2
from ai_engine_v3.models import Article, QualityScores

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("quick_test")


def build_article_objects(curated):
    articles: list[Article] = []
    for art in curated:
        qs = QualityScores(
            quality_score=art.quality_score,
            relevance_score=art.relevance_score,
            importance_score=art.importance_score,
            total_score=art.total_score,
        )
        articles.append(
            Article(
                original_article_title=art.original_data.get("title", ""),
                original_article_link=art.original_data.get("link", ""),
                original_article_published_date=art.original_data.get("published", ""),
                source_name=art.original_data.get("source_name", "unknown"),
                quality_scores=qs,
                original_article_content=art.original_data.get("content", ""),
            )
        )
    return articles


def main(limit: int):
    logger.info("\n🔍 Running quick test pipeline – limit %d", limit)

    scraper = SmartScraper()
    raw_articles = scraper.comprehensive_scrape()

    curator = CuratorV2()
    curated = curator.curate(raw_articles)[:limit]
    logger.info("Selected %d curated articles for test", len(curated))

    pending = build_article_objects(curated)

    proc = ProcessorV2()
    proc.batch_process(pending)

    # Simple human-readable summary
    for art in pending:
        logger.info("\n=== %s ===", art.simplified_english_title or art.original_article_title)
        logger.info("Context block:\n%s", art.context_block or "<none>")
        logger.info("Explanations keys: %s", list((art.contextual_title_explanations or {}).keys())[:10])

    logger.info("\n💰 Total cost: $%.4f", proc.total_cost_usd)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Quick Better-French AI pipeline test")
    ap.add_argument("--limit", type=int, default=5, help="Number of fresh articles to process (default 5)")
    args = ap.parse_args()

    sys.exit(main(args.limit)) 