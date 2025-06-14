from __future__ import annotations

"""Minimal MCP server (Phase 1)

Run locally:
    uvicorn mcp_server.main:app --reload --port 8000

The server exposes one endpoint:
POST /chat {"user_id": str, "message": str}

It keeps per-user chat history in memory, builds a prompt that includes the
recent conversation, calls the LLM via OpenRouter, and returns the reply.
"""

import os
from typing import Dict, List
from pathlib import Path
import subprocess

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
if not OPENROUTER_API_KEY:
    raise RuntimeError(
        "Environment variable OPENROUTER_API_KEY is required to start MCP server"
    )

PRIMARY_MODEL = "meta-llama/llama-3-70b-instruct"  # keep in sync with pipeline
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# We keep the last N messages per user in memory (Phase 1).
HISTORY_LENGTH = 10

# Path to website JSON feed (relative to repo root)
ROLLING_JSON_PATH = (
    Path(__file__).resolve().parent.parent
    / "Project-Better-French-Website"
    / "rolling_articles.json"
)

# ---------------------------------------------------------------------------
# Pydantic models (request / response)
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str
    total_tokens: int | None = None
    cost_usd: float | None = None


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

chat_history: Dict[str, List[Dict[str, str]]] = {}


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Better-French MCP", version="0.1.0")


@app.get("/status")
async def status():
    """Return live article count for quick site status checks."""
    return {"live_articles": get_live_article_count()}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Return an LLM response and save context."""

    # Build conversation context
    history = chat_history.get(req.user_id, [])[-HISTORY_LENGTH:]
    messages = history + [
        {"role": "user", "content": req.message},
    ]

    # Lightweight built-in answers (skip LLM) ---------------------------------
    lower_msg = req.message.lower()
    if "how many" in lower_msg and "article" in lower_msg:
        count = get_live_article_count()
        reply_text = f"There are currently {count} AI-enhanced articles live on the site."
        return ChatResponse(reply=reply_text, total_tokens=0, cost_usd=0.0)

    # Call OpenRouter
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": PRIMARY_MODEL,
        "messages": messages,
        "max_tokens": 700,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(f"{OPENROUTER_BASE_URL}/chat/completions", json=payload, headers=headers)
            r.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"OpenRouter error: {exc}")

    data = r.json()
    reply = data["choices"][0]["message"]["content"].strip()

    # Save to history
    chat_history.setdefault(req.user_id, []).append({"role": "user", "content": req.message})
    chat_history[req.user_id].append({"role": "assistant", "content": reply})

    usage = data.get("usage", {})
    total_tokens = usage.get("total_tokens")

    # Estimate cost just like pipeline
    input_cost_per_1k = 0.00035
    output_cost_per_1k = 0.00070
    cost_usd: float | None = None
    if usage:
        cost_usd = (usage.get("prompt_tokens", 0) / 1000) * input_cost_per_1k + (
            usage.get("completion_tokens", 0) / 1000
        ) * output_cost_per_1k

    return ChatResponse(reply=reply, total_tokens=total_tokens, cost_usd=cost_usd)


# ---------------------------------------------------------------------------
# Helper: count live articles
# ---------------------------------------------------------------------------


def get_live_article_count() -> int:
    """Return number of articles in rolling_articles.json. 0 if file missing."""
    # Always try to sync the local repo so the count is up-to-date with GitHub.
    try:
        subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=Path(__file__).resolve().parent.parent,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
            check=False,
        )
    except Exception:
        # Ignore network or git errors; we'll just use local file.
        pass

    try:
        import json

        with ROLLING_JSON_PATH.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
        if isinstance(data, list):
            return len(data)
        # Old format (dict with "articles")
        if isinstance(data, dict) and "articles" in data:
            return len(data["articles"])
    except FileNotFoundError:
        return 0
    except Exception:
        return 0
    return 0 