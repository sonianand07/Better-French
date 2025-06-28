#!/usr/bin/env python3
"""High-tier verification pass for AI-Engine v4.

This script reviews articles that already went through the fast v3-style
processing step and upgrades them to 100 % tooltip coverage using GPT-4o (or
any model specified via ``AI_ENGINE_HIGH_MODEL``).

Run manually or from the CI pipeline:

    python scripts/verify_news.py

Prerequisites:
    • OPENROUTER_API_KEY exported (for GPT-4o access via OpenRouter)
    • The v4 pending store must exist (created by previous pipeline steps)
"""
from __future__ import annotations

import itertools, json, logging, pathlib, sys
from typing import List, Iterable

# Local imports -------------------------------------------------------------
from ai_engine_v4.storage import Storage
from ai_engine_v4.client import HighLLMClient
from ai_engine_v4.prompt_loader import render
from ai_engine_v4.models import Article
from ai_engine_v3.validator import expected_tokens_from_title  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("verify_news")

BATCH_SIZE = 3  # Articles per verifier call (optimise context vs. cost)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _chunked(seq: List[Article], size: int) -> Iterable[List[Article]]:
    """Yield *seq* in chunks of length *size*."""
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def _build_prompt(article: Article) -> str:
    """Render review_tooltips prompt for a single *article*."""
    # Normalise explanations to JSON string for the prompt
    explanations_json = json.dumps(article.contextual_title_explanations, ensure_ascii=False, indent=2)
    return render(
        "review_tooltips.jinja",
        original_title=article.original_article_title,
        fr_title=article.simplified_french_title or "",
        en_title=article.simplified_english_title or "",
        fr_summary=article.french_summary or "",
        en_summary=article.english_summary or "",
        explanations_json=explanations_json,
    )


def _apply_fixes(article: Article, payload: dict) -> Article:
    """Merge *payload* from verifier into *article* in-place and return it."""
    fixed = payload.get("fixed_tokens", [])
    missing = payload.get("missing_tokens", [])
    updates = payload.get("updated_titles_summaries", {})

    # Ensure explanations dict exists
    explanations = article.contextual_title_explanations or {}
    if not isinstance(explanations, dict):
        explanations = {}

    def _to_dict_list(lst):
        if not lst:
            return []
        if isinstance(lst, list):
            return lst
        return []

    for obj in itertools.chain(_to_dict_list(fixed), _to_dict_list(missing)):
        if not isinstance(obj, dict):
            continue
        word = obj.get("original_word")
        if not word or not isinstance(word, str):
            continue
        explanations[word] = {k: v for k, v in obj.items() if k != "original_word"}

    article.contextual_title_explanations = explanations

    # Update titles/summaries if present
    for field in (
        "simplified_french_title",
        "simplified_english_title",
        "french_summary",
        "english_summary",
    ):
        val = updates.get(field)
        if val and isinstance(val, str):
            setattr(article, field, val.strip())

    # Final flag
    article.quality_checked = True
    return article


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def main():
    pending = [a for a in Storage.load_pending() if not getattr(a, "quality_checked", False)]
    if not pending:
        logger.info("No articles pending verification – all caught up.")
        return

    logger.info("🔍 %d articles need verification", len(pending))
    llm = HighLLMClient()
    verified: List[Article] = []

    for batch in _chunked(pending, BATCH_SIZE):
        for art in batch:
            prompt = _build_prompt(art)
            messages = [
                {"role": "system", "content": "You are Better French high-tier verifier."},
                {"role": "user", "content": prompt},
            ]
            reply = llm.chat(messages, temperature=0.2, max_tokens=1800)
            if not reply:
                logger.warning("Verifier replied empty for article: %s", art.original_article_title[:60])
                continue
            try:
                payload = json.loads(reply)
            except json.JSONDecodeError as e:
                logger.warning("JSON parse error for verifier reply: %s – %s", art.original_article_title[:60], e)
                continue

            try:
                art = _apply_fixes(art, payload)
            except Exception as e:
                logger.error("Failed applying fixes to '%s': %s", art.original_article_title[:60], e)
                continue
            verified.append(art)

    if not verified:
        logger.info("0 articles could be verified – aborting save.")
        return

    # Merge back into pending store
    existing = Storage.load_pending()
    merged: dict[str, Article] = {a.original_article_link: a for a in existing}
    for upd in verified:
        merged[upd.original_article_link] = upd

    Storage.save_pending(list(merged.values()))
    # Also refresh rolling feed to ensure website sees updated explanations
    try:
        Storage.save_rolling(Storage.load_rolling() + verified)
    except Exception as e:
        logger.warning("Could not update rolling feed: %s", e)
    logger.info("✅ Successfully verified %d articles", len(verified))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("Interrupted by user") 