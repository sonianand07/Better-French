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
    expected_tokens_from_title,
)

logger = logging.getLogger(__name__)


class ProcessorV2:
    def __init__(self, model: str | None = None):
        # Passing None lets LLMClient fall back to env override or the new
        # default "google/gemini-2.5-flash".
        self.llm = LLMClient(model=model)
        self.total_cost_usd: float = 0.0  # crude running total

    # ---------------- Prompt helpers (placeholder) ----------------
    def _render_title_prompt(self, article: Article) -> str:
        return render("simplify_titles_summaries.jinja", title=article.original_article_title)

    def _render_explain_prompt(self, article: Article) -> str:
        tokens = list(expected_tokens_from_title(article.original_article_title))
        return render(
            "contextual_words_v2.jinja",
            title=article.original_article_title,
            tokens=tokens,
        )

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
    def _chat_with_validation(self, messages, render_fn, article: Article, validate_fn, max_attempts: int = 3):
        """Send chat completion and ensure *validate_fn* passes.

        If the first attempt fails JSON validation we send a follow-up user
        message: *"Your previous reply was invalid JSON… output ONLY valid
        JSON."* and retry once.
        """
        for attempt in range(max_attempts):
            if attempt > 0:
                # Overwrite last user message with explicit correction:
                #  – reiterate English-heading rule
                #  – demand valid JSON only
                messages[-1]["content"] = (
                    render_fn(article)
                    + "\n\nCRITICAL: The bold heading BEFORE the colon must be a concise ENGLISH translation (1–3 words, capitalised) and must NOT repeat the French token or contain accents.  Respond ONLY with valid JSON and no markdown fences."
                )
            response = self.llm.chat(messages)
            self._add_cost(self.llm.last_usage)
            ok, payload, _reason = validate_fn(response or "")
            if ok and payload:
                return True, payload
        return False, None

    # ---------------- Cost helpers ----------------
    def _estimate_cost(self, usage: dict) -> float:
        """Return USD cost for one OpenRouter response based on token usage."""
        if not usage:
            return 0.0
        # Pricing table: (input per 1k, output per 1k)
        PRICE_TABLE = {
            "anthropic/claude-3.5-sonnet": (0.00300, 0.01500),
            "meta-llama/llama-3-70b-instruct": (0.00035, 0.00070),
            "google/gemini-2.5-flash": (0.00025, 0.00050),
            "google/gemini-2-flash": (0.00025, 0.00050),
            "mistralai/mistral-medium-3": (0.00040, 0.00200),
        }
        in_price, out_price = PRICE_TABLE.get(self.llm.model, (0.00300, 0.01500))
        prompt_t = usage.get("prompt_tokens", 0)
        comp_t = usage.get("completion_tokens", 0)
        return (prompt_t / 1000) * in_price + (comp_t / 1000) * out_price

    def _add_cost(self, usage: dict):
        self.total_cost_usd += self._estimate_cost(usage)

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
            msg_stack, self._render_explain_prompt, article, validate_explanations_payload, max_attempts=4
        )

        if ok2 and payload2:
            # Convert list → dict keyed by the word itself (website expects that)
            if isinstance(payload2, list):
                safe_items = [
                    obj
                    for obj in payload2
                    if isinstance(obj, dict) and isinstance(obj.get("original_word"), str)
                ]
                article.contextual_title_explanations = {
                    obj["original_word"]: {k: v for k, v in obj.items() if k != "original_word"}
                    for obj in safe_items
                }
            else:
                article.contextual_title_explanations = payload2

        else:
            logger.warning(
                "Explanations missing or invalid for '%s' – storing without contextual words",
                article.original_article_title[:60],
            )
            article.backfill_attempts += 1

        # From v3-1.1 onward we accept any article that has simplified titles & summaries
        # as 'display-ready'. Contextual words are a nice-to-have, not a blocker.
        article.display_ready = True
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

        # 2. Append *all* processed articles to rolling feed. ``Storage.save_rolling``
        #    itself will prioritise fully display-ready items, but will gracefully
        #    fall back to ``ai_enhanced`` ones if none are ready.  This guarantees
        #    the website always has some content even when contextual
        #    explanations are missing.
        Storage.save_rolling(Storage.load_rolling() + processed)
        logger.info("Processed %d articles", len(processed))
        logger.info("💰 Total LLM cost this batch: $%.4f", self.total_cost_usd)