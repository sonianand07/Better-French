"""High-level orchestrator for AI-Engine v2."""
from __future__ import annotations

import logging, hashlib, json
from typing import List

from .models import Article
from .client import LLMClient
from .storage import Storage

logger = logging.getLogger(__name__)


class ProcessorV2:
    def __init__(self, model: str = "meta-llama/llama-3-70b-instruct"):
        self.llm = LLMClient(model=model)

    # ---------------- Prompt helpers (placeholder) ----------------
    def _render_title_prompt(self, article: Article) -> str:
        return f"Simplify and translate title: {article.original_article_title}"

    def _render_explain_prompt(self, article: Article) -> str:
        return f"Provide contextual explanations for: {article.original_article_title}"

    # ---------------- Core processing ----------------
    def process_article(self, article: Article) -> Article:
        # Step 1 titles & summaries
        messages = [
            {"role": "system", "content": "You are Better French AI assistant."},
            {"role": "user", "content": self._render_title_prompt(article)},
        ]
        resp1 = self.llm.chat(messages)
        if resp1:
            # Placeholder parse logic
            article.simplified_french_title = article.original_article_title  # TODO parse
            article.simplified_english_title = article.original_article_title
            article.french_summary = "..."  # TODO
            article.english_summary = "..."
        # Step 2 explanations
        messages[1]["content"] = self._render_explain_prompt(article)
        resp2 = self.llm.chat(messages)
        if resp2:
            article.contextual_title_explanations = []  # TODO parse
        article.ai_enhanced = True
        return article

    def batch_process(self, pending: List[Article]):
        processed: List[Article] = []
        for art in pending:
            try:
                processed.append(self.process_article(art))
            except Exception as e:
                logger.error("Failed to process article %s: %s", art.original_article_title[:50], e)
        # Save
        Storage.save_rolling(Storage.load_rolling() + processed)
        logger.info("Processed %d articles", len(processed)) 