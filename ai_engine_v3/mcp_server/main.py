from __future__ import annotations
"""Better French – MCP (monitor-control platform) v3

Provides lightweight HTTP endpoints so ops dashboards or Cron monitors can
track whether the static site is fresh and whether the CI pipeline is healthy.

Run locally:
    uvicorn ai_engine_v3.mcp_server.main:app --reload --port 8001

Env vars:
    OPENROUTER_API_KEY   – required only for /chat .
    GITHUB_TOKEN         – (optional) allows authenticated calls to GitHub REST
                            for higher rate-limit when querying workflow runs.
    BF_ROLLING_PATH      – (optional) path to rolling_articles.json; defaults to
                            ai_engine_v3/website/rolling_articles.json
"""
import json, os, subprocess, datetime
from pathlib import Path
from typing import List, Dict, Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]  # ~/Project Better French
DEFAULT_ROLLING = REPO_ROOT / "ai_engine_v3" / "website" / "rolling_articles.json"
ROLLING_JSON_PATH = Path(os.getenv("BF_ROLLING_PATH", DEFAULT_ROLLING))

GITHUB_REPO = os.getenv("GITHUB_REPOSITORY", "sonianand07/Better-French")
GITHUB_WORKFLOW_FILENAME = "auto_update_v3.yml"  # file that owns the publish job
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
CHAT_MODEL = "mistralai/mistral-medium-3"

# ---------------------------------------------------------------------------
# Util helpers
# ---------------------------------------------------------------------------

def git_pull_fast() -> None:
    """Keep local repo fresh – ignore any errors when offline."""
    try:
        subprocess.run(["git", "pull", "--ff-only"], cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    except Exception:
        pass


def load_articles() -> List[Dict[str, Any]]:
    """Return list of article dicts or empty list."""
    if not ROLLING_JSON_PATH.exists():
        return []
    with ROLLING_JSON_PATH.open("r", encoding="utf-8") as fp:
        data = json.load(fp)
    if isinstance(data, dict):
        return data.get("articles", [])
    if isinstance(data, list):
        return data
    return []


def latest_processed_at(articles: List[Dict[str, Any]]) -> str | None:
    dates = [a.get("processed_at") or a.get("original_article_published_date") for a in articles if a]
    return max(dates) if dates else None

# ---------------------------------------------------------------------------
# GitHub helpers – minimal
# ---------------------------------------------------------------------------
async def fetch_last_workflow_run() -> Dict[str, Any] | None:
    """Return last completed run of the publish workflow (success or failure)."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW_FILENAME}/runs?per_page=1&status=completed"
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            runs = resp.json().get("workflow_runs", [])
            return runs[0] if runs else None
        except httpx.HTTPError:
            return None

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)

class ChatResponse(BaseModel):
    reply: str
    tokens: int | None = None
    cost_usd: float | None = None

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Better French MCP", version="0.2.0")

@app.get("/status")
async def status():
    """Return basic site stats (count, newest article time)."""
    git_pull_fast()
    arts = load_articles()
    return {
        "live_articles": len(arts),
        "updated_at": latest_processed_at(arts),
        "latest_title": arts[0].get("simplified_english_title") if arts else None,
    }

@app.get("/articles")
async def articles(limit: int = Query(20, ge=1, le=100)):
    """Return the N most recent articles (for quick QA)."""
    git_pull_fast()
    arts = load_articles()[:limit]
    return arts

@app.get("/ci")
async def ci():
    """Return metadata of the last completed publish workflow run."""
    run = await fetch_last_workflow_run()
    if not run:
        raise HTTPException(status_code=502, detail="Cannot fetch workflow runs from GitHub")
    return {
        "id": run.get("id"),
        "status": run.get("conclusion"),
        "finished_at": run.get("updated_at"),
        "html_url": run.get("html_url"),
        "head_sha": run.get("head_sha"),
    }

@app.get("/freshness")
async def freshness():
    """Compare site updated_at vs last successful CI finish time."""
    arts = load_articles()
    site_time_str = latest_processed_at(arts)
    run = await fetch_last_workflow_run()
    ci_time_str = run.get("updated_at") if run else None
    if not site_time_str or not ci_time_str:
        raise HTTPException(status_code=502, detail="Insufficient data to assess freshness")
    site_dt = datetime.datetime.fromisoformat(site_time_str.replace("Z", "+00:00"))
    ci_dt = datetime.datetime.fromisoformat(ci_time_str.replace("Z", "+00:00"))
    delta_min = (ci_dt - site_dt).total_seconds() / 60
    return {
        "site_updated": site_dt.isoformat(),
        "ci_finished": ci_dt.isoformat(),
        "delta_minutes": delta_min,
        "status": "ok" if abs(delta_min) < 20 else "stale",
    }

# ---------------------------------------------------------------------------
# Simple chat passthrough (optional)
# ---------------------------------------------------------------------------

chat_history: Dict[str, List[Dict[str, str]]] = {}
HIST = 10

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=400, detail="OPENROUTER_API_KEY not set on server")
    hist = chat_history.get(req.user_id, [])[-HIST:]
    msgs = hist + [{"role": "user", "content": req.message}]
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    }
    payload = {"model": CHAT_MODEL, "messages": msgs, "max_tokens": 700, "temperature": 0.7}
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(f"{OPENROUTER_BASE}/chat/completions", json=payload, headers=headers)
            r.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"OpenRouter error: {exc}")
    data = r.json()
    reply = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})
    # cost estimate (mistral-medium)
    cost = (usage.get("prompt_tokens", 0)/1000)*0.0004 + (usage.get("completion_tokens", 0)/1000)*0.002
    chat_history.setdefault(req.user_id, []).extend([
        {"role": "user", "content": req.message},
        {"role": "assistant", "content": reply},
    ])
    return ChatResponse(reply=reply, tokens=usage.get("total_tokens"), cost_usd=round(cost,4)) 