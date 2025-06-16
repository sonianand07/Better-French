"""Storage helper for AI-Engine v2.
Manages pending_articles.json and rolling_articles.json with automatic backup.
"""
from __future__ import annotations

import json, shutil, datetime, pathlib
from typing import List

from .models import Article

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEBSITE_DIR = ROOT / "Project-Better-French-Website"
DATA_DIR = ROOT / "data" / "live"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PENDING_FILE = DATA_DIR / "pending_articles.json"
ROLLING_FILE = WEBSITE_DIR / "rolling_articles.json"
BACKUP_DIR = WEBSITE_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)


class Storage:
    """Handle article persistence for engine v2."""

    @staticmethod
    def _load(path: pathlib.Path) -> List[Article]:
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        articles = raw.get("articles", []) if isinstance(raw, dict) else raw
        return [Article.parse_obj(a) for a in articles]

    @staticmethod
    def _save(path: pathlib.Path, articles: List[Article]):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"articles": [a.dict(by_alias=True) for a in articles]}, f, ensure_ascii=False, indent=2)

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
        # enforce top 100 display-ready
        ready = [a for a in articles if a.display_ready]
        ready.sort(key=lambda a: a.processed_at or "", reverse=True)
        cls._save(ROLLING_FILE, ready[:100]) 