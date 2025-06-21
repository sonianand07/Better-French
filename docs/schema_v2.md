# Better French – Article JSON schema v2

_Last updated: 2025-06-16_

This document describes the **canonical JSON structure** produced by AI-Engine v2 and consumed by the static website and downstream analytics.

```jsonc
{
  "schema_version": 2,
  "id": "uuid4",
  "original_article_title": "string",
  "original_article_link": "url",
  "original_article_published_date": "ISO-8601",
  "source_name": "string",
  "quality_scores": {
    "quality_score": 0.0,
    "relevance_score": 0.0,
    "importance_score": 0.0,
    "total_score": 0.0
  },
  "difficulty": "A1 | A2 | B1 | B2 | C1 | C2 | null",
  "tone": "neutral | opinion | satire | other | null",
  "keywords": ["string"],
  "audio_url": "url|null",
  "simplified_french_title": "string|null",
  "simplified_english_title": "string|null",
  "french_summary": "markdown|null",
  "english_summary": "markdown|null",
  "contextual_title_explanations": [
    {
      "original_word": "string",
      "display_format": "string (can include **markdown**)",
      "explanation": "string",
      "cultural_note": "string|null"
    }
  ],
  "key_vocabulary": [
    {"word": "string", "definition": "string", "example": "string"}
  ],
  "cultural_context": {"any": "json"},
  "processed_at": "ISO-8601",
  "processing_id": "string|null",
  "ai_enhanced": true,
  "display_ready": true
}
```

Notes
-----
* **Minimal display-ready** requires:
  1. `simplified_french_title`
  2. `simplified_english_title`
  3. `contextual_title_explanations` (≥ 1 entry)
* Additional optional fields may be `null` until the corresponding pipeline steps are implemented.
* `schema_version` is pinned at **2** so clients can safely branch on structure changes.

Validation rules are implemented in `ai_engine_v2/validator.py` and unit-tested in `tests/ai_engine_v2/`. 