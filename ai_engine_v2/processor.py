"""High-level orchestrator for AI-Engine v2."""
from __future__ import annotations

import logging, hashlib, json, re
from typing import List

from .models import Article
from .client import LLMClient
from .storage import Storage
from .prompt_loader import render
from .validator import (
    validate_titles_payload,
    validate_explanations_payload,
    article_is_display_ready,
    coverage_ok,
)

logger = logging.getLogger(__name__)


class ProcessorV2:
    def __init__(self, model: str = "meta-llama/llama-3-70b-instruct"):
        self.llm = LLMClient(model=model)
        self.total_cost_usd: float = 0.0  # crude running total

    # ---------------- Prompt helpers (placeholder) ----------------
    def _render_title_prompt(self, article: Article) -> str:
        return render("simplify_titles_summaries.jinja", title=article.original_article_title)

    def _render_explain_prompt(self, article: Article) -> str:
        return render("contextual_words.jinja", title=article.original_article_title)

    def _safe_json(self, text: str):
        """Extract first JSON object/array from text."""
        match = re.search(r"({[\s\S]+}|\[[\s\S]+])", text)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    # ---------------- internal helpers ----------------
    def _chat_with_validation(self, messages, render_fn, article: Article, validate_fn, max_attempts: int = 2):
        """Send chat completion and ensure *validate_fn* passes.

        If the first attempt fails JSON validation we send a follow-up user
        message: *"Your previous reply was invalid JSON… output ONLY valid
        JSON."* and retry once.
        """
        for attempt in range(max_attempts):
            if attempt > 0:
                # overwrite last user message with explicit instructions
                messages[-1]["content"] = (
                    render_fn(article)
                    + "\n\nRespond ONLY with valid JSON and no markdown fences."
                )
            response = self.llm.chat(messages)
            ok, payload, _reason = validate_fn(response or "")
            if ok and payload:
                return True, payload
        return False, None

    # ---------------- Core processing ----------------
    def process_article(self, article: Article) -> Article:
        # ----- TITLES phase with retry -----
        msg_stack = [
            {"role": "system", "content": "You are Better French AI assistant."},
            {"role": "user", "content": self._render_title_prompt(article)},
        ]
        ok1, payload1 = self._chat_with_validation(
            msg_stack, self._render_title_prompt, article, validate_titles_payload
        )
        if not ok1:
            logger.error(
                "Title prompt failed validation for '%s'", article.original_article_title[:60]
            )
            return article  # skip – keep non-enhanced
        article.simplified_french_title = payload1["simplified_french_title"]
        article.simplified_english_title = payload1["simplified_english_title"]
        article.french_summary = payload1["french_summary"]
        article.english_summary = payload1["english_summary"]
        article.difficulty = payload1["difficulty"]
        article.tone = payload1["tone"]

        # ----- EXPLANATIONS phase with retry -----
        msg_stack[1]["content"] = self._render_explain_prompt(article)
        ok2, payload2 = self._chat_with_validation(
            msg_stack, self._render_explain_prompt, article, validate_explanations_payload
        )

        if ok2 and payload2:
            # Convert list to dict keyed by original_word to match website expectations
            if isinstance(payload2, list):
                article.contextual_title_explanations = {
                    obj.get("original_word"): {k: v for k, v in obj.items() if k != "original_word"}
                    for obj in payload2 if isinstance(obj, dict) and obj.get("original_word")
                }
            else:
                article.contextual_title_explanations = payload2
            # Coverage guard (allow small gaps)
            if not coverage_ok(article.original_article_title, article.contextual_title_explanations):
                logger.warning(
                    "Coverage not perfect for '%s' – will accept but mark not display-ready",
                    article.original_article_title[:60],
                )
                article.display_ready = False
        else:
            logger.warning("Explanations failed validation for '%s'", article.original_article_title[:60])
            article.backfill_attempts += 1

        article.ai_enhanced = True
        return article

    def batch_process(self, pending: List[Article]):
        processed: List[Article] = []
        for idx, art in enumerate(pending, 1):
            try:
                logger.info("🔧 Processing AI enhancements %d/%d", idx, len(pending))
                new_art = self.process_article(art)
                # Accept any article that received *some* AI enhancement
                if new_art.ai_enhanced or article_is_display_ready(new_art):
                    processed.append(new_art)
            except Exception as e:
                logger.error("Failed to process article %s: %s", art.original_article_title[:50], e)
        # Persist changes -----------------------------------------------------------------
        # 1. Update pending store (overwrite articles with same link)
        pending_existing = Storage.load_pending()
        merged: dict[str, Article] = {a.original_article_link: a for a in pending_existing}
        for upd in processed:
            merged[upd.original_article_link] = upd
        Storage.save_pending(list(merged.values()))

        # 2. Append display-ready to rolling feed
        Storage.save_rolling(Storage.load_rolling() + [a for a in processed if a.display_ready])
        logger.info("Processed %d articles", len(processed)) 