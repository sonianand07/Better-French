"""Storage helper for AI-Engine v2.
Manages pending_articles.json and rolling_articles.json with automatic backup.
"""
from __future__ import annotations

import json, shutil, datetime, pathlib
from typing import List

from .models import Article

# Use ai_engine_v2 package root as base so the engine can live standalone
ROOT = pathlib.Path(__file__).resolve().parent  # ai_engine_v2/

# Website & data paths become siblings of the code, making the package portable
WEBSITE_DIR = ROOT / "website"
DATA_DIR = ROOT / "data" / "live"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PENDING_FILE = DATA_DIR / "pending_articles.json"
ROLLING_FILE = WEBSITE_DIR / "rolling_articles.json"
BACKUP_DIR = WEBSITE_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


class Storage:
    """Handle article persistence for engine v2."""

    @staticmethod
    def _load(path: pathlib.Path) -> List[Article]:
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        articles = raw.get("articles", []) if isinstance(raw, dict) else raw
        parsed = []
        for item in articles:
            try:
                parsed.append(Article.parse_obj(item))
            except Exception:
                # skip entries that don't match v2 schema
                continue
        return parsed

    @staticmethod
    def _save(path: pathlib.Path, articles: List[Article]):
        serializable = [a.model_dump(mode="json", by_alias=True) for a in articles]
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"articles": serializable}, f, ensure_ascii=False, indent=2)

    # Public helpers -------------------------------------------------------
    @classmethod
    def load_pending(cls) -> List[Article]:
        return cls._load(PENDING_FILE)

    @classmethod
    def load_rolling(cls) -> List[Article]:
        return cls._load(ROLLING_FILE)

    @classmethod
    def save_pending(cls, articles: List[Article]):
        cls._save(PENDING_FILE, articles)

    @classmethod
    def save_rolling(cls, articles: List[Article]):
        # backup current
        if ROLLING_FILE.exists():
            ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(ROLLING_FILE, BACKUP_DIR / f"rolling_{ts}.json")
        # Prefer fully display-ready first, but fall back to partially enhanced
        ready = [a for a in articles if a.display_ready]

        # If no fully ready articles, include those that at least have simplified titles
        if not ready:
            ready = [a for a in articles if a.ai_enhanced]

        # Final safety: if still empty (unlikely) keep originals to avoid empty site
        if not ready:
            ready = articles

        ready.sort(key=lambda a: a.processed_at or "", reverse=True)
        cls._save(ROLLING_FILE, ready[:100]) 