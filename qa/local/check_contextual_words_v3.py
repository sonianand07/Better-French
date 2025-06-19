#!/usr/bin/env python3
"""V3 version of contextual-word smoke test (identical logic, different default path)."""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.append('.')  # ensure local imports
from qa.local.check_contextual_words import main as _base_main  # reuse logic

DEFAULT_V3_PATH = Path(__file__).resolve().parent.parent.parent / "ai_engine_v3" / "website" / "rolling_articles.json"

if __name__ == "__main__":
    # Inject default path and run base script
    sys.argv.extend(["--path", str(DEFAULT_V3_PATH)])
    _base_main() 