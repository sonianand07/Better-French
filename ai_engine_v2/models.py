from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field, HttpUrl, validator


class QualityScores(BaseModel):
    quality_score: float = Field(..., ge=0, le=10)
    relevance_score: float = Field(..., ge=0, le=10)
    importance_score: float = Field(..., ge=0, le=10)
    total_score: float = Field(..., ge=0, le=30)


class ContextualExplanation(BaseModel):
    original_word: str
    display_format: str
    explanation: str
    cultural_note: Optional[str] = ""


class Article(BaseModel):
    """Unified representation for curated and AI-enhanced articles."""

    # Original article information
    original_article_title: str
    original_article_link: HttpUrl
    original_article_published_date: str  # keep string for now
    source_name: str

    # Quality metadata (may come from curator)
    quality_scores: QualityScores

    # AI-enhanced fields (optional until processed)
    simplified_french_title: Optional[str] = None
    simplified_english_title: Optional[str] = None
    french_summary: Optional[str] = None
    english_summary: Optional[str] = None
    contextual_title_explanations: Optional[List[ContextualExplanation]] = None
    key_vocabulary: Optional[List[Dict[str, Any]]] = None
    cultural_context: Optional[Dict[str, Any]] = None

    # Processing metadata
    processed_at: Optional[str] = None
    processing_id: Optional[str] = None

    # Flags
    ai_enhanced: bool = False
    display_ready: bool = False

    @validator("display_ready", always=True)
    def _derive_display_ready(cls, v, values):
        """Article is ready if it has simplified titles AND contextual explanations."""
        if v:
            return v
        required = (
            values.get("simplified_french_title")
            and values.get("simplified_english_title")
            and values.get("contextual_title_explanations")
        )
        return bool(required)

    @validator("processed_at", pre=True, always=True)
    def _default_processed_at(cls, v):
        if v is None:
            return datetime.utcnow().isoformat(timespec="seconds")
        return v 