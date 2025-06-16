"""High-level orchestrator for AI-Engine v2."""
from __future__ import annotations

import logging, hashlib, json, re
from typing import List

from .models import Article
from .client import LLMClient
from .storage import Storage
from .prompt_loader import render

logger = logging.getLogger(__name__)


class ProcessorV2:
    def __init__(self, model: str = "meta-llama/llama-3-70b-instruct"):
        self.llm = LLMClient(model=model)

    # ---------------- Prompt helpers (placeholder) ----------------
    def _render_title_prompt(self, article: Article) -> str:
        return render("titles_summaries.jinja", title=article.original_article_title)

    def _render_explain_prompt(self, article: Article) -> str:
        return render("explanations.jinja", title=article.original_article_title)

    def _safe_json(self, text: str):
        """Extract first JSON object/array from text."""
        match = re.search(r"({[\s\S]+}|\[[\s\S]+])", text)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    # ---------------- Core processing ----------------
    def process_article(self, article: Article) -> Article:
        # Step 1 titles & summaries
        messages = [
            {"role": "system", "content": "You are Better French AI assistant."},
            {"role": "user", "content": self._render_title_prompt(article)},
        ]
        resp1 = self.llm.chat(messages)
        if resp1:
            data = self._safe_json(resp1)
            if isinstance(data, dict):
                article.simplified_french_title = data.get("simplified_french_title")
                article.simplified_english_title = data.get("simplified_english_title")
                article.french_summary = data.get("french_summary")
                article.english_summary = data.get("english_summary")
        # Step 2 explanations
        messages[1]["content"] = self._render_explain_prompt(article)
        resp2 = self.llm.chat(messages)
        if resp2:
            data2 = self._safe_json(resp2)
            article.contextual_title_explanations = data2 if isinstance(data2, list) else None
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