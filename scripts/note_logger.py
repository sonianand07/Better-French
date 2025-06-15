#!/usr/bin/env python3
"""Utility used by automation scripts to append a single task row
   to today's daily-notes markdown table.

   Usage from any script:
       from scripts.note_logger import log_task
       log_task("Quality repair", "Fixed 12 missing tokens", status="done")

   The helper:
   • Creates docs/daily_notes/<YYYY-MM-DD>.md if missing.
   • Ensures the file starts with a table header.
   • Appends one markdown table row per call.
   • Never deletes/edits previous lines (append-only safeguard).
"""
from __future__ import annotations

import datetime
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
NOTES_DIR = ROOT / "docs" / "daily_notes"
HEADER = (
    "# Daily Notes\n\n"
    "| Task | Purpose / Details | Status |\n"
    "|------|-------------------|--------|\n"
)

def log_task(task: str, purpose: str, status: str = "done") -> None:
    """Append a task row to today's daily-note file."""
    date_str = datetime.date.today().isoformat()
    note_path = NOTES_DIR / f"{date_str}.md"
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    if not note_path.exists():
        note_path.write_text(HEADER, encoding="utf-8")

    row = f"| {task} | {purpose} | {status.upper()} |\n"
    with open(note_path, "a", encoding="utf-8") as fp:
        fp.write(row)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python scripts/note_logger.py <task> <purpose> [status]", file=sys.stderr)
        sys.exit(1)
    log_task(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "done") 