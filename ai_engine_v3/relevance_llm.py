from __future__ import annotations
"""LLM-based relevance scorer for Better French v3."""

import logging
import config.api_config  # noqa: F401 side-effect
from ai_engine_v3.client import LLMClient

logger = logging.getLogger(__name__)

_PROMPT = (
    "You are ranking French and world news for an expat professional living in France. "
    "Profile: tech industry, interested in energy policy and major world events. "
    "On a scale 0-10 (10 = extremely relevant), rate the relevance of the following headline:\n"
    "HEADLINE: \"{headline}\"\n\nRespond with ONLY the number."
)

_llm = LLMClient(model="mistralai/mistral-large-2411")

# Cost constants for current model (USD per 1k tokens)
_IN_PRICE = 0.00200
_OUT_PRICE = 0.00600

def score(headline: str):
    """Return (score, usd_cost) tuple."""
    msg = [{"role": "user", "content": _PROMPT.format(headline=headline)}]
    try:
        reply = _llm.chat(msg, max_tokens=5, temperature=0)
        if reply:
            value = float(reply.strip())
            if 0 <= value <= 10:
                # cost estimate based on last_usage
                usage = _llm.last_usage or {}
                in_t = usage.get("prompt_tokens", 0)
                out_t = usage.get("completion_tokens", 0)
                usd = (in_t/1000)*_IN_PRICE + (out_t/1000)*_OUT_PRICE
                return value, usd
    except Exception as e:
        logger.warning("LLM relevance scoring failed: %s", e)
    return 0.0, 0.0 