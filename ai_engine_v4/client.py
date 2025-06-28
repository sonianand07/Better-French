"""LLM client wrappers for AI-Engine v4.

We reuse the lightweight ``LLMClient`` from v3 for fast-generation and add
``HighLLMClient`` which defaults to a higher-tier model (GPT-4o or Claude-Opus
with web search) for the verification pass.
"""

from __future__ import annotations

import os

from ai_engine_v3.client import LLMClient  # type: ignore


class HighLLMClient(LLMClient):
    """High-tier model with browsing/search capabilities.

    Defaults can be overridden via the ``AI_ENGINE_HIGH_MODEL`` environment
    variable so we can A/B test between GPT-4o, Claude-Opus etc.  We keep the
    same OpenRouter API wrapper for simplicity – any model name accepted by
    OpenRouter will work.
    """

    def __init__(self, model: str | None = None):
        # Prefer explicit arg, then env var, then sensible default
        high_default = os.getenv("AI_ENGINE_HIGH_MODEL", "openai/gpt-4o-mini")
        super().__init__(model=model or high_default) 