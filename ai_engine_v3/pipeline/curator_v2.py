from __future__ import annotations
"""Curator v2 – filters & scores articles for expat professionals in France."""
import re, logging
from typing import List, Any

import spacy
from spacy.language import Language

from .config import HIGH_RELEVANCE_KEYWORDS, MEDIUM_RELEVANCE_KEYWORDS, CURATOR_WEIGHTS
from .scraper import NewsArticle

logger = logging.getLogger(__name__)

try:
    _NLP: Language = spacy.load("fr_core_news_sm")
except Exception:
    _NLP = spacy.blank("fr")


class ScoredArticleV2:
    def __init__(self, original: NewsArticle, relevance: float, practical: float, newsworthiness: float):
        self.original_data = original.__dict__
        self.relevance_score = relevance
        self.practical_score = practical
        self.newsworthiness_score = newsworthiness
        # Alias for compatibility with QualityScores model
        self.importance_score = newsworthiness
        self.total_score = (
            relevance * CURATOR_WEIGHTS["relevance"]
            + practical * CURATOR_WEIGHTS["practical"]
            + newsworthiness * CURATOR_WEIGHTS["newsworthiness"]
        )
        # Rescale to 0-10 for QualityScores model (max theoretical 30)
        self.quality_score = round(min(self.total_score / 3, 10.0), 3)


class CuratorV2:
    """Assign scores and keep only high-value articles."""

    def __init__(self, profile: 'UserProfile | None' = None):
        from ..profile import UserProfile  # local import to avoid cycle
        self.profile = profile
        self.high_kw = set(HIGH_RELEVANCE_KEYWORDS)
        self.medium_kw = set(MEDIUM_RELEVANCE_KEYWORDS)
        self.profile_kw = set()
        if profile:
            self.profile_kw.update({w.lower() for w in profile.work_domains})
            self.profile_kw.update({w.lower() for w in profile.pain_points})
            self.profile_kw.update({w.lower() for w in profile.interests})

    # ----------------------------------------------------- scoring helpers
    def _score_relevance(self, text: str, is_global: bool = False) -> float:
        txt = text.lower()
        if is_global:
            return 8.0
        if any(kw in txt for kw in self.high_kw):
            return 9.0
        if any(kw in txt for kw in self.medium_kw):
            return 7.0
        # France-wide catch-all so big national topics aren't missed
        if "france" in txt or "français" in txt:
            return 7.0
        if self.profile_kw and any(kw in txt for kw in self.profile_kw):
            return 6.0
        return 4.0

    def _score_practical(self, text: str) -> float:
        doc = _NLP(text)
        ent_types = {ent.label_ for ent in doc.ents}
        score = 0
        if "MONEY" in ent_types:
            score += 3
        if "DATE" in ent_types:
            score += 2
        if "PERCENT" in ent_types:
            score += 1
        if "ORG" in ent_types:
            score += 1
        return min(score, 9)

    def _score_newsworthiness(self, art: NewsArticle) -> float:
        # crude heuristic: longer summary -> higher
        length = len(art.summary.split()) if art.summary else 0
        return 6 + min(length / 100, 4)

    # ----------------------------------------------------- public API
    def curate(self, raw_articles: List[NewsArticle]) -> List[ScoredArticleV2]:
        scored: List[ScoredArticleV2] = []
        for art in raw_articles:
            rel = self._score_relevance(art.title + " " + art.summary, art.global_event)
            prac = self._score_practical(art.summary or art.title)
            news = self._score_newsworthiness(art)
            scored.append(ScoredArticleV2(art, rel, prac, news))

        # Filter by total threshold 10 – tuned empirically
        approved = [a for a in scored if a.total_score >= 10]
        logger.info("CuratorV2 approved %d/%d articles", len(approved), len(scored))

        # Cap global-event items to 5 to avoid overload
        globals_only = [a for a in approved if a.original_data.get("global_event") or getattr(a.original_data, 'global_event', False)]
        if len(globals_only) > 5:
            # sort globals by total_score and keep top 5
            globals_only.sort(key=lambda x: x.total_score, reverse=True)
            globals_top = globals_only[:5]
            # keep all non-global approved items
            non_globals = [a for a in approved if a not in globals_only]
            approved = globals_top + non_globals

        return approved 