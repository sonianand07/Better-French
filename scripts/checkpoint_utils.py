#!/usr/bin/env python3
"""Helpers for atomic checkpointing of article batch progress.

A single JSON file stored at ``temp/batch_WIP.json`` keeps the list of
completed AI-processed articles plus a ``cursor`` (index of next
article to process).  All writes are atomic (via ``Path.replace``) so
we never leave a half-written file.

Functions here are imported by the AI-Engine and scheduler to
persist / resume work across job restarts.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_PATH = Path("temp/batch_WIP.json")


def load_checkpoint(path: Path | str = DEFAULT_PATH) -> Dict[str, Any]:
    """Return existing checkpoint or an empty structure."""
    p = Path(path)
    if not p.exists():
        return {"cursor": 0, "articles": []}
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Corrupt file – rename for post-mortem and start fresh
        p.rename(p.with_suffix(".corrupt"))
        return {"cursor": 0, "articles": []}


def save_checkpoint(data: Dict[str, Any], path: Path | str = DEFAULT_PATH) -> None:
    """Atomically write *data* to *path*."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    tmp.replace(p)


def append_article(article: Dict[str, Any], path: Path | str = DEFAULT_PATH) -> None:
    """Append one processed article to the checkpoint file."""
    data = load_checkpoint(path)
    data.setdefault("articles", []).append(article)
    data["cursor"] = len(data["articles"])
    save_checkpoint(data, path)


def clear_checkpoint(path: Path | str = DEFAULT_PATH) -> None:
    Path(path).unlink(missing_ok=True) 