from __future__ import annotations
"""AI-Engine v2 response validator & cleaner.

This helper ensures the raw LLM output is valid JSON and fills the required
fields of an ``Article`` before it is accepted for production.  By isolating
this logic we can unit-test edge-cases and keep ``processor.py`` simple.
"""

import json, logging, re
from typing import Tuple, Optional, List, Dict, Any

from .models import Article

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Core validation helpers
# ---------------------------------------------------------------------------

def _extract_first_json(text: str) -> Optional[str]:
    """Return the first valid JSON object/array substring in *text*.

    A lot of LLMs wrap JSON in markdown fences or add commentary. We search
    for the first balanced {...} or [...] block and return it (as a string).
    """
    # very naive but works for our prompts
    # match either { .... } or [ .... ] non-greedy, including newlines
    match = re.search(r"({[\s\S]+?}|\[[\s\S]+?])", text)
    if match:
        return match.group(0)
    return None


def validate_titles_payload(raw_text: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Validate LLM answer for titles+summaries prompt.

    Returns (ok, payload_or_None, reason) where *payload* is a dict ready to
    be merged into an Article instance.
    """
    json_str = _extract_first_json(raw_text)
    if not json_str:
        return False, None, "No JSON found"
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return False, None, f"JSON decode error: {e}"

    # ------------------------------------------------------------------
    # v2 schema includes extra context fields. We accept either v1 or v2
    # as long as all *base* keys exist; the new keys are mandatory for v2.
    # ------------------------------------------------------------------

    base_keys = {
        "simplified_french_title",
        "simplified_english_title",
        "french_summary",
        "english_summary",
        "difficulty",
        "tone",
    }

    has_context = "context_summary_en" in data or "key_facts" in data

    # All base keys must be present
    if not base_keys.issubset(data):
        return False, None, "Missing required keys"

    if has_context:
        if "context_summary_en" not in data or "key_facts" not in data:
            return False, None, "Missing context fields"
        # Validate word limits (simple split on whitespace)
        if len(data["context_summary_en"].split()) > 80:
            return False, None, "Context summary too long"
        # key_facts list requirements
        key_facts = data["key_facts"]
        if not isinstance(key_facts, list):
            return False, None, "key_facts must be a list"
        if not (3 <= len(key_facts) <= 8):
            return False, None, "key_facts length invalid"
        if any((not isinstance(item, str) or len(item) > 80 or not item.strip()) for item in key_facts):
            return False, None, "Invalid key_facts item(s)"

    # Title length ≤ 70 chars each
    if len(data["simplified_french_title"]) > 70 or len(data["simplified_english_title"]) > 70:
        return False, None, "Title too long"

    # Summary 30–40 words (allow slight tolerance ±2)
    for field in ("french_summary", "english_summary"):
        words = data[field].split()
        if not (28 <= len(words) <= 42):
            return False, None, f"{field} word count out of range"

    # CEFR & tone validation
    if data["difficulty"] not in {"A1", "A2", "B1", "B2", "C1", "C2"}:
        return False, None, "Invalid difficulty"
    if data["tone"] not in {"neutral", "opinion", "satire", "other"}:
        return False, None, "Invalid tone"

    return True, data, "ok"


def validate_explanations_payload(raw_text: str) -> Tuple[bool, Optional[Any], str]:
    """Validate LLM answer for contextual explanations prompt.

    Accepts either:
    • a JSON list of objects `{original_word, display_format, explanation, cultural_note?}`
    • a JSON dict keyed by *original_word* mapping to a nested dict with the other fields.
    """
    json_str = _extract_first_json(raw_text)
    if not json_str:
        return False, None, "No JSON found"
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return False, None, f"JSON decode error: {e}"

    # -------- list format --------
    if isinstance(data, list):
        cleaned: List[Dict[str, Any]] = []
        for obj in data:
            if not isinstance(obj, dict):
                return False, None, "Non-dict item"
            if not {"original_word", "display_format", "explanation"}.issubset(obj):
                return False, None, "Missing keys in item"
            cleaned.append(obj)
        return True, cleaned, "ok"

    # -------- dict format --------
    if isinstance(data, dict):
        # Every value must itself be a dict containing display_format+explanation
        for word, val in data.items():
            if not isinstance(val, dict):
                return False, None, "Dict value is not an object"
            if not {"display_format", "explanation"}.issubset(val):
                return False, None, "Missing keys in value object"
        return True, data, "ok"

    return False, None, "Unexpected JSON structure"


# ---------------------------------------------------------------------------
# Proper-noun coverage helpers (ported from v1)
# ---------------------------------------------------------------------------

_CAP_RE = re.compile(r"(?:[A-Z][\w'’.-]+(?:\s+[A-Z][\w'’.-]+){0,4})")

def _merge_proper_nouns(title: str) -> str:
    """Collapse multi-word proper names to preserve them as single tokens."""
    def repl(match):
        return match.group(0).replace(" ", " ")  # NBSP join to keep as one chunk

    return _CAP_RE.sub(repl, title)

def expected_tokens_from_title(title: str) -> set[str]:
    text = _merge_proper_nouns(title)
    tokens = set()
    # Split on whitespace but keep punctuation tokens
    for tok in re.findall(r"\w+'\w+|\w+|[«»\":,.;?!]", text):
        tok = tok.replace(" ", " ")  # restore normal space
        if tok:
            tokens.add(tok)
    return tokens

def coverage_ok(title: str, explanations: list[dict[str, str]] | dict, *, max_missing: int = 3, max_missing_ratio: float = 0.2) -> bool:
    """Return True if coverage is good enough.

    We allow a small gap because LLMs sometimes legitimately skip stop-words or
    punctuation.  Defaults: ≤3 tokens or ≤20 % of expected tokens can be
    missing.
    """
    expected = expected_tokens_from_title(title)
    if isinstance(explanations, dict):
        provided = set(explanations.keys())
    else:
        provided = {d.get("original_word") for d in explanations if isinstance(d, dict)}
    missing = expected - provided
    if not missing:
        return True

    # quick ratio / absolute threshold
    if len(missing) <= max_missing:
        logger.debug("Coverage ok with small gap (%d tokens)", len(missing))
        return True
    if len(missing) / max(len(expected), 1) <= max_missing_ratio:
        logger.debug("Coverage ok with %.0f%% gap", 100 * len(missing) / len(expected))
        return True

    logger.debug("Coverage insufficient, missing tokens: %s", missing)
    return False

# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------

def article_is_display_ready(article: Article) -> bool:
    """Return True if an Article passes final readiness checks."""
    # The Article instance has already been validated during instantiation.
    # If stricter checks are needed, they can be added here.
    return article.display_ready 