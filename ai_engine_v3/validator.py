from __future__ import annotations
"""AI-Engine v2 response validator & cleaner.

This helper ensures the raw LLM output is valid JSON and fills the required
fields of an ``Article`` before it is accepted for production.  By isolating
this logic we can unit-test edge-cases and keep ``processor.py`` simple.
"""

import json, logging, re
from typing import Tuple, Optional, List, Dict, Any
import json as _json, pathlib as _pl

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

    required_keys = {
        "simplified_french_title",
        "simplified_english_title",
        "french_summary",
        "english_summary",
        "difficulty",
        "tone",
    }
    if not required_keys.issubset(data.keys()):
        return False, None, "Missing required keys"
    # quick length checks – keep summaries ≤ 400 chars each
    if len(data["french_summary"]) > 800 or len(data["english_summary"]) > 800:
        return False, None, "Summary too long"

    # CEFR and tone validation
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
            # Extra rule: heading before the colon must be English (no accents & not identical to original)
            disp = obj.get("display_format", "")
            if not _english_heading_ok(disp, obj["original_word"]):
                return False, None, "Heading not English in display_format"
        return True, cleaned, "ok"

    # -------- dict format --------
    if isinstance(data, dict):
        # Every value must itself be a dict containing display_format+explanation
        for word, val in data.items():
            if not isinstance(val, dict):
                return False, None, "Dict value is not an object"
            if not {"display_format", "explanation"}.issubset(val):
                return False, None, "Missing keys in value object"
            if not _english_heading_ok(val["display_format"], word):
                return False, None, "Heading not English in display_format"
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

# ---------------------------------------------------------------------------
# New helper: detect French-looking heading
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"\*\*([^:]+):")

# Load mini glossary (case-insensitive keys)
_GLOSSARY_PATH = _pl.Path(__file__).resolve().parents[0] / "data" / "mini_glossary.json"
try:
    _GLOSSARY = {k.lower(): v.lower() for k, v in _json.loads(_GLOSSARY_PATH.read_text(encoding="utf-8")).items()}
except Exception:
    _GLOSSARY = {}

def _english_heading_ok(display_format: str, original_word: str) -> bool:
    """Return False if the heading still looks French.

    Criteria:
    • Heading identical (case-insensitive) to *original_word*
    • Heading contains accented characters À-ÿ
    """
    if not display_format:
        return False
    m = _HEADING_RE.match(display_format)
    if not m:
        return False
    heading = m.group(1).strip()
    if heading.lower() == (original_word or "").lower():
        return False
    if re.search(r"[À-ÿ]", heading):
        return False
    # Dictionary cross-check – if we know the canonical translation, they must match
    canon = _GLOSSARY.get(original_word.lower())
    if canon and heading.lower() != canon:
        return False
    return True 