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

        # Allow dynamic override so we can A/B different LLMs without code edits.
        # Priority: explicit arg > env var AI_ENGINE_MODEL > default (Gemini 2.5 Flash)
        if model is None:
            model = os.getenv("AI_ENGINE_MODEL", "google/gemini-flash-2.5-128k")
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
        for attempt in range(1, retries + 1):
            try:
                r = self.session.post(f"{self.base}/chat/completions", json=payload, timeout=30)
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"].strip()
                logger.warning("OpenRouter HTTP %s: %s", r.status_code, r.text[:120])
            except requests.RequestException as e:
                logger.warning("Request error: %s", e)
            # wait & retry
            sleep_for = backoff * (2 ** (attempt - 1)) + random.uniform(0, 1)
            time.sleep(sleep_for)
        logger.error("LLM chat failed after %d attempts", retries)
        return None 