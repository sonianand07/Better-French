"""Thin OpenRouter/LLM client with retry & backoff"""
from __future__ import annotations

import requests, time, random, logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, model: str | None = None, api_base: str = "https://openrouter.ai/api/v1"):
        self.base = api_base
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {self._get_api_key()}"
        # Add proper identification headers
        self.session.headers["HTTP-Referer"] = "https://github.com/sonianand07/Better-French"
        self.session.headers["X-Title"] = "Better French - Educational Platform"
        self.session.headers["User-Agent"] = "BetterFrench/1.0"

        # Store latest token usage dict from API responses so callers can
        # estimate costs.  Structure: {"prompt_tokens": int, "completion_tokens": int, ...}
        self.last_usage: Dict[str, int] = {}

        # Allow dynamic override so we can A/B different LLMs without code edits.
        # Priority: explicit arg > env var AI_ENGINE_MODEL > default (Gemini 2.5 Flash)
        if model is None:
            model = os.getenv("AI_ENGINE_MODEL", "mistralai/mistral-medium-3")
        self.model = model

    def _get_api_key(self) -> str:
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY env var not set")
        return key

    def chat(self, messages: list[dict[str, str]], max_tokens: int = 1500, temperature: float = 0.7, retries: int = 3) -> Optional[str]:
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        backoff = 2
        # Reset usage for this call
        self.last_usage: Dict[str, int] = {}
        fallback_model = "google/gemini-2.5-flash"
        switched = False  # ensure we only switch once
        for attempt in range(1, retries + 1):
            try:
                r = self.session.post(f"{self.base}/chat/completions", json=payload, timeout=30)
                if r.status_code == 200:
                    data = r.json()
                    # Store token usage so the caller can estimate cost
                    self.last_usage = data.get("usage", {}) or {}
                    return data["choices"][0]["message"]["content"].strip()
                # Invalid-model guard → switch to fallback once
                if (
                    r.status_code == 400
                    and "not a valid model" in r.text.lower()
                    and not switched
                    and self.model != fallback_model
                ):
                    logger.warning("Model '%s' invalid – falling back to %s", self.model, fallback_model)
                    self.model = fallback_model
                    switched = True
                    continue  # retry immediately with fallback

                logger.warning("OpenRouter HTTP %s: %s", r.status_code, r.text[:120])
            except requests.RequestException as e:
                logger.warning("Request error: %s", e)
            # wait & retry
            sleep_for = backoff * (2 ** (attempt - 1)) + random.uniform(0, 1)
            time.sleep(sleep_for)
        logger.error("LLM chat failed after %d attempts", retries)
        return None 