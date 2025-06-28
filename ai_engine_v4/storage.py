"""Storage helper for AI-Engine v4.

Extends v3 logic but works with the new Article model (adds ``quality_checked``)
so pending & rolling files remain compatible.
"""
from __future__ import annotations

import json, shutil, datetime, pathlib
from typing import List

from .models import Article

# Package root
ROOT = pathlib.Path(__file__).resolve().parent
# Website & data paths remain sibling directories to keep package self-contained
WEBSITE_DIR = ROOT / "website"
DATA_DIR = ROOT / "data" / "live"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PENDING_FILE = DATA_DIR / "pending_articles.json"
ROLLING_FILE = WEBSITE_DIR / "rolling_articles.json"
BACKUP_DIR = WEBSITE_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


class Storage:
    """Handle article persistence for engine v4 (same format as v3)."""

    # --- Internal generic helpers --------------------------------------
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
                # skip entries that don't match v4 schema
                continue
        return parsed

    @staticmethod
    def _save(path: pathlib.Path, articles: List[Article]):
        serializable = [a.model_dump(mode="json", by_alias=True) for a in articles]
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"articles": serializable}, f, ensure_ascii=False, indent=2)
        tmp.replace(path)

    # --- Public helpers -------------------------------------------------
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
        # Create backup of existing rolling file first
        if ROLLING_FILE.exists():
            ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(ROLLING_FILE, BACKUP_DIR / f"rolling_{ts}.json")

        # Deduplicate by link and keep newest version
        dedup: dict[str, Article] = {}
        for art in sorted(articles, key=lambda a: a.processed_at or "", reverse=True):
            dedup.setdefault(art.original_article_link, art)

        pool = list(dedup.values())

        # Prefer articles fully display-ready *and* quality-checked
        ready = [a for a in pool if a.display_ready and a.quality_checked]

        # Fallback to display_ready only, then ai_enhanced, then original
        if not ready:
            ready = [a for a in pool if a.display_ready]
        if not ready:
            ready = [a for a in pool if a.ai_enhanced]
        if not ready:
            ready = pool

        def _date_key(article: Article):
            return article.original_article_published_date or article.processed_at or ""

        ready.sort(key=_date_key, reverse=True)
        cls._save(ROLLING_FILE, ready[:200]) 