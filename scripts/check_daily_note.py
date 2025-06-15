#!/usr/bin/env python3
"""Pre-commit helper – ensure today's daily note exists and contains the log table.

Usage (from .githooks/pre-commit):
    python scripts/check_daily_note.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

NOTES_DIR = Path("docs/daily_notes")

def main() -> int:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    note_path = NOTES_DIR / f"{today}.md"

    if not note_path.exists():
        print(f"❌ Pre-commit abort: today's note {note_path} is missing.")
        print("Run: cp docs/daily_notes/template.md", note_path)
        return 1

    content = note_path.read_text(encoding="utf-8")
    if "| File | Type | Reason |" not in content:
        print("❌ Pre-commit abort: 'File change log' table missing in today's note.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main()) 