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

PKG_ROOT = pathlib.Path(__file__).resolve().parent.parent  # ai_engine_v3/
RAW_DIR = PKG_ROOT / "data" / "raw_archive"
STATE_FILE = PKG_ROOT / "data" / "state.json"
OVERFLOW_FILE = PKG_ROOT / "data" / "live" / "overflow.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Publication caps
# ------------------------------------------------------------------
# BF_PER_RUN_CAP (env) keeps the hourly batch small (default 20 -> 5 in CI).
# BF_DAILY_CAP controls the total allowed in one calendar day.
#   • If unset, "0", "none" or "unlimited"  ⇒  no daily ceiling (effectively ∞).
#   • Otherwise, use the integer value provided.

_daily_cap_raw = os.getenv("BF_DAILY_CAP", "").strip().lower()

if _daily_cap_raw in {"", "0", "none", "unlimited"}:
    # No daily limit
    DAILY_CAP = 999_999  # a very large number that we will never hit
else:
    try:
        DAILY_CAP = int(_daily_cap_raw)
    except ValueError:
        DAILY_CAP = 999_999  # fallback – treat as unlimited

MIN_RULE_SCORE = float(os.getenv("BF_MIN_RULE_SCORE", "12"))

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

    # 4. LLM relevance score  (only for fresh candidates) --------------
    blended: list[tuple[float, Any]] = []  # (score, curator_obj)
    rel_cost_total = 0.0
    if fresh:
        logger.info("Scoring relevance for %d candidate articles via LLM …", len(fresh))

    for idx, art in enumerate(fresh, 1):
        if len(fresh) <= 40 or idx % 10 == 1:
            logger.info("  [LLM] %3d/%d · %s", idx, len(fresh), art.original_data.get("title", "")[:80])

        rel, usd = llm_score(art.original_data.get("title", ""))
        rel_cost_total += usd
        blended_score = 0.6 * art.total_score + 0.4 * rel
        # attach for downstream use
        art.original_data["blended_score"] = blended_score
        art.original_data["queued_at"] = datetime.datetime.utcnow().isoformat()
        blended.append((blended_score, art))

    blended.sort(key=lambda x: x[0], reverse=True)

    # ------------------------------------------------------------------
    # 5. Load overflow queue -------------------------------------------
    # ------------------------------------------------------------------
    carry_over: list[tuple[float, dict]] = []
    if OVERFLOW_FILE.exists():
        try:
            overflow_payload = json.loads(OVERFLOW_FILE.read_text())
            for item in overflow_payload:
                score = item.get("score", 0)
                data = item.get("article") or {}
                ts = item.get("queued_at") or item.get("saved_at")
                # expire after 24h
                if ts:
                    try:
                        age_h = (datetime.datetime.utcnow() - datetime.datetime.fromisoformat(ts)).total_seconds() / 3600.0
                        if age_h > 24:
                            continue
                    except Exception:
                        pass
                # skip if already on site
                if data.get("link") in existing_links:
                    continue
                carry_over.append((score, data))
        except Exception as e:
            logger.warning("Could not read overflow queue: %s", e)

    # ------------------------------------------------------------------
    # 6. Merge pools and choose top ------------------------------------
    # ------------------------------------------------------------------
    pool: list[tuple[float, Any]] = carry_over + [(sc, art.original_data) for sc, art in blended]
    pool.sort(key=lambda x: x[0], reverse=True)

    PER_RUN_CAP = int(os.getenv("BF_PER_RUN_CAP", "20"))

    # honour both limits: daily and per-run
    remaining_slots = min(PER_RUN_CAP, DAILY_CAP - state["published_today"])

    if remaining_slots <= 0:
        logger.info("Run skipped – cap reached (daily %d or per-run %d)", DAILY_CAP, PER_RUN_CAP)
        return

    # After bucket filtering we now have pool already; apply same bucket logic? For simplicity keep old logic on pool order.
    selected_raw = pool[:remaining_slots]
    leftover_raw = pool[remaining_slots:100]  # cap queue to 100

    selected = []
    for score, data in selected_raw:
        if isinstance(data, dict):
            selected.append(data)
        else:  # curator object
            selected.append(data.original_data)

    # save overflow
    try:
        out_items = [
            {
                "score": sc,
                "article": d if isinstance(d, dict) else d.original_data,
                "queued_at": (d.get("queued_at") if isinstance(d, dict) else datetime.datetime.utcnow().isoformat()),
            }
            for sc, d in leftover_raw
        ]
        OVERFLOW_FILE.parent.mkdir(parents=True, exist_ok=True)
        OVERFLOW_FILE.write_text(json.dumps(out_items, ensure_ascii=False, indent=2))
    except Exception as e:
        logger.warning("Could not write overflow queue: %s", e)

    # Convert curator objects to Article model expected by Processor
    def _to_article(data_in):
        # data_in may be dict (from queue) or curator obj
        if not isinstance(data_in, dict):
            data = data_in.original_data.copy()
            qual = getattr(data_in, "quality_score", None)
            rel_sc = getattr(data_in, "relevance_score", None)
            imp_sc = getattr(data_in, "importance_score", None)
            total_sc = getattr(data_in, "total_score", None)
        else:
            data = data_in.copy()
            qs = data.get("quality_scores", {})
            qual = qs.get("quality_score")
            rel_sc = qs.get("relevance_score")
            imp_sc = qs.get("importance_score")
            total_sc = qs.get("total_score")
        data["quality_scores"] = {
            "quality_score": round(qual, 3) if qual is not None else 5.0,
            "relevance_score": round(rel_sc, 3) if rel_sc is not None else 5.0,
            "importance_score": round(imp_sc, 3) if imp_sc is not None else 5.0,
            "total_score": round(total_sc, 3) if total_sc is not None else 15.0,
        }
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