#!/usr/bin/env python3
"""Qualify raw news into a capped, profile-tuned daily batch and run AI processing.
Run every 1-2 hours.
"""
from __future__ import annotations

import pathlib, json, datetime, logging, os, sys

from ai_engine_v3.pipeline.curator_v2 import CuratorV2
from ai_engine_v3.relevance_llm import score as llm_score
from ai_engine_v3.storage import Storage
from ai_engine_v3.processor import ProcessorV2
from ai_engine_v3.models import Article

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # repo root
RAW_DIR = ROOT / "data" / "raw_archive"
STATE_FILE = ROOT / "ai_engine_v3" / "data" / "state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Allow env override for experiments
DAILY_CAP = int(os.getenv("BF_DAILY_CAP", "20"))
MIN_RULE_SCORE = float(os.getenv("BF_MIN_RULE_SCORE", "14"))

# ----------------------------------------------------- state helpers

def _load_state():
    if not STATE_FILE.exists():
        # Fresh install: skip historical backlog by marking the latest raw file as already processed.
        latest = ""
        try:
            latest_path = max(RAW_DIR.rglob("*_delta.json"), key=lambda p: p.name, default=None)
            if latest_path is not None:
                latest = latest_path.name
        except Exception:
            pass  # ignore probing errors – fall back to empty string
        state = {"last_delta": latest, "published_today": 0, "date": datetime.date.today().isoformat()}
        # Persist baseline so future runs are incremental
        try:
            STATE_FILE.write_text(json.dumps(state))
        except Exception:
            pass
        return state
    return json.loads(STATE_FILE.read_text())

def _save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state))

# ----------------------------------------------------- main

def main():
    state = _load_state()
    today = datetime.date.today().isoformat()
    if state.get("date") != today:
        state["published_today"] = 0
        state["date"] = today

    # 1. gather new delta files ------------------------------------
    last_delta = state.get("last_delta", "")
    new_paths = sorted(
        (p for p in RAW_DIR.rglob("*_delta.json") if p.name > last_delta),
        key=lambda p: p.name,
    )

    if not new_paths:
        logger.info("No new delta files to process.")
        return

    raw_articles = []
    from ai_engine_v3.pipeline.scraper import NewsArticle  # type: ignore
    for path in new_paths:
        data = json.loads(path.read_text())
        articles_list = data.get("articles") if isinstance(data, dict) else data
        for d in articles_list or []:
            try:
                raw_articles.append(NewsArticle(**d))
            except Exception:
                continue

    logger.info("Loaded %d raw articles from %d new files", len(raw_articles), len(new_paths))

    # 2. rule-based curator filter -------------------------------
    curator = CuratorV2()
    prelim = curator.curate(raw_articles)
    prelim = [a for a in prelim if a.total_score >= MIN_RULE_SCORE]
    logger.info("%d articles passed rule filter (score ≥ %.1f)", len(prelim), MIN_RULE_SCORE)

    # 3. skip links already on site ------------------------------
    existing_links = {a.original_article_link for a in Storage.load_rolling()}
    fresh = [a for a in prelim if a.original_data.get("link") not in existing_links]

    logger.info("%d articles remain after removing already-published links", len(fresh))

    # 4. LLM relevance score -------------------------------------
    blended = []
    rel_cost_total = 0.0
    logger.info("Scoring relevance for %d candidate articles via LLM …", len(fresh))

    for idx, art in enumerate(fresh, 1):
        # Give the operator a clear, human-friendly progress line.
        if len(fresh) <= 40 or idx % 10 == 1:
            logger.info("  [LLM] %3d/%d · %s", idx, len(fresh), art.original_data.get("title", "")[:80])

        rel, usd = llm_score(art.original_data.get("title", ""))
        rel_cost_total += usd
        blended_score = 0.6 * art.total_score + 0.4 * rel
        blended.append((blended_score, art))

    blended.sort(key=lambda x: x[0], reverse=True)

    PER_RUN_CAP = int(os.getenv("BF_PER_RUN_CAP", "20"))

    # honour both limits: daily and per-run
    remaining_slots = min(PER_RUN_CAP, DAILY_CAP - state["published_today"])

    if remaining_slots <= 0:
        logger.info("Run skipped – cap reached (daily %d or per-run %d)", DAILY_CAP, PER_RUN_CAP)
        return

    # Bucket balancing -------------------------------------------------
    work_kw = {"tech", "énergie", "energy", "numérique", "digital", "ia", "start-up", "startup"}

    work, global_news, france_general = [], [], []
    for _score, art in blended:
        title_lower = art.original_data.get("title", "").lower()
        if art.original_data.get("global_event"):
            global_news.append(art)
        elif any(k in title_lower for k in work_kw):
            work.append(art)
        else:
            france_general.append(art)

    def take(lst, n):
        out, rest = lst[:n], lst[n:]
        return out, rest

    need_work = min(10, remaining_slots)
    need_global = min(10, remaining_slots - need_work)

    pick_work, work = take(work, need_work)
    pick_global, global_news = take(global_news, need_global)

    remaining = remaining_slots - len(pick_work) - len(pick_global)
    filler_pool = work + global_news + france_general
    selected = pick_work + pick_global + filler_pool[:remaining]

    logger.info("Selected %d articles for today (cap %d) – %d work, %d world, %d other",
                len(selected), DAILY_CAP, len(pick_work), len(pick_global), len(selected)-len(pick_work)-len(pick_global))

    # Convert curator objects to Article model expected by Processor
    def _to_article(obj):
        data = obj.original_data.copy()
        # Ensure required quality_scores field exists and is proper dataclass
        if isinstance(data.get("quality_scores"), dict):
            qs_dict = data["quality_scores"]
        else:
            qs_dict = {
                "quality_score": round(obj.quality_score, 3) if hasattr(obj, "quality_score") else 5.0,
                "relevance_score": round(obj.relevance_score, 3) if hasattr(obj, "relevance_score") else 5.0,
                "importance_score": round(obj.importance_score, 3) if hasattr(obj, "importance_score") else 5.0,
                "total_score": round(obj.total_score, 3) if hasattr(obj, "total_score") else 15.0,
            }
        data["quality_scores"] = qs_dict
        # Map mandatory Article keys if missing
        if "original_article_title" not in data and data.get("title"):
            data["original_article_title"] = data.pop("title")
        if "original_article_link" not in data and data.get("link"):
            data["original_article_link"] = data.pop("link")
        if "original_article_published_date" not in data:
            data["original_article_published_date"] = data.get("published_parsed") or data.get("published") or datetime.datetime.utcnow().isoformat()
        if "source_name" not in data and data.get("source_name"):
            data["source_name"] = data["source_name"]

        # Remove keys that Article model doesn't expect but keep via **extras? (ignored) though pydantic will error unknown field? model allows extra? Not specified; remove noisy keys.
        for k in ["scraped_at", "content", "image_url", "image_title", "source_url", "feed_url", "guid", "language", "tags", "category", "global_event", "breaking_news", "urgency_score", "metadata", "article_hash", "content_hash", "author", "published", "published_parsed", "original_data"]:
            data.pop(k, None)

        # Provide defaults
        data.setdefault("schema_version", 2)
        data.setdefault("id", None)
        return Article(**data)

    art_objects = [_to_article(obj) for obj in selected]

    proc = ProcessorV2()
    proc.batch_process(art_objects)

    # 6. update state -------------------------------------------
    state["published_today"] += len(selected)
    state["last_delta"] = new_paths[-1].name
    _save_state(state)
    logger.info("Done. Published today: %d / %d", state["published_today"], DAILY_CAP)

    logger.info("💰 Relevance LLM cost: $%.4f | Processor cost: $%.4f", rel_cost_total, proc.total_cost_usd)

    sys.stdout.write("\n")

if __name__ == "__main__":
    main() 