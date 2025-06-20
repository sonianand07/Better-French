from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any, Optional, Literal, Union

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
    """Unified representation for curated and AI-enhanced articles (schema v2)."""

    # Schema + identity ----------------------------------------------------------------
    schema_version: Literal[2] = 2  # JSON schema version
    id: Optional[str] = Field(None, description="UUID4 assigned after initial curation")

    # Original article information
    original_article_title: str
    original_article_link: HttpUrl
    original_article_published_date: str  # keep string for now
    source_name: str

    # Quality metadata (may come from curator)
    quality_scores: QualityScores

    # --- New v2 metadata --------------------------------------------------------------
    difficulty: Optional[str] = Field(None, pattern="^(A1|A2|B1|B2|C1|C2)$")
    tone: Optional[str] = Field(
        None,
        pattern="^(neutral|opinion|satire|other)$",
        description="Text tone classification",
    )
    keywords: Optional[List[str]] = None
    audio_url: Optional[HttpUrl] = None

    # AI-enhanced fields (optional until processed)
    simplified_french_title: Optional[str] = None
    simplified_english_title: Optional[str] = None
    french_summary: Optional[str] = None
    english_summary: Optional[str] = None
    # Accept both list (new schema) and dict (legacy website format)
    contextual_title_explanations: Optional[
        Union[List[ContextualExplanation], Dict[str, Dict[str, str]]]
    ] = None
    key_vocabulary: Optional[List[Dict[str, Any]]] = None
    cultural_context: Optional[Dict[str, Any]] = None

    # Processing metadata
    processed_at: Optional[str] = None
    processing_id: Optional[str] = None

    # Flags
    ai_enhanced: bool = False
    display_ready: bool = False

    # Back-fill tracking
    backfill_attempts: int = 0  # how many times we tried to repair explanations

    # ----------------------------- Validators -----------------------------
    @validator("display_ready", always=True)
    def _derive_display_ready(cls, v, values):
        """Article is ready if it has simplified titles AND contextual explanations."""
        if v:
            return v
        required = (
            values.get("simplified_french_title")
            and values.get("simplified_english_title")
            and values.get("contextual_title_explanations") is not None
        )
        return bool(required)

    @validator("processed_at", pre=True, always=True)
    def _default_processed_at(cls, v):
        if v is None:
            return datetime.utcnow().isoformat(timespec="seconds")
        return v

    class Config:
        schema_extra = {
            "example": {
                "schema_version": 2,
                "id": "b71bd0b7-3c6c-4dab-b0e1-281e0c7f6d14",
                "original_article_title": "Réforme des retraites: le gouvernement maintient le cap",
                "original_article_link": "https://www.lemonde.fr/politique/article/2025/06/16/reforme-retraites.html",
                "original_article_published_date": "2025-06-16T08:22:00Z",
                "source_name": "Le Monde",
                "quality_scores": {
                    "quality_score": 8.2,
                    "relevance_score": 7.5,
                    "importance_score": 6.1,
                    "total_score": 21.8,
                },
                "difficulty": "B2",
                "tone": "neutral",
                "keywords": ["retraite", "manifestation", "gouvernement"],
                "simplified_french_title": "Réforme des retraites: le cap est maintenu",
                "simplified_english_title": "Pension reform: government stays the course",
                "french_summary": "Le gouvernement persiste à vouloir réformer le système...",
                "english_summary": "The government insists on reforming the pension system...",
                "contextual_title_explanations": [
                    {
                        "original_word": "retraite",
                        "display_format": "**retraite**",
                        "explanation": "pension, retirement",
                    }
                ],
                "ai_enhanced": True,
                "display_ready": True,
            }
        } 