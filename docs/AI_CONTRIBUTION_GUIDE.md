# AI Contribution Guide

This repository is collaboratively maintained by humans **and** language-model assistants.  To keep everyone aligned, please follow the rules below whenever an AI session makes changes.

---

## 1. Read before you write

1. Open the latest daily note in `docs/daily_notes/` (they are named `YYYY-MM-DD.md`).
2. Skim any relevant architecture docs in `docs/` referenced by that note.
3. Only then begin coding or documentation changes.

## 2. Keep a daily engineering log

At the end of every working session **create or update** today's note using the template provided (see next section).

Each note **must** contain:

* **What we accomplished today** – bullet list of key tasks/fixes.
* **Pain points / issues encountered** – anything that blocked or slowed us.
* **Action items for tomorrow** – prioritised TODOs.
* **File change log (why)** – table listing each file touched (or created) and why.

Save notes in UTC date order inside `docs/daily_notes/`.

## 3. Use the template

A ready-made stub lives at `docs/daily_notes/template.md`.  Copy and rename it to the current date before filling it in.

## 4. Commit policy

* **Code + notes belong in the *same* commit.**  No PR should modify code without an accompanying daily note update.
* If a session touches no code but only research/analysis, it should *still* produce a note (even if very short).

## 5. Pre-commit hook (optional but recommended)

A helper script at `scripts/check_daily_note.py` verifies that a note for *today* exists and has a "File change log" section.  It is wired into `.githooks/pre-commit` – enable it by running:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
```

With the hook enabled, a commit aborts if today's note is missing.

## 6. Respect the repository

* Do **not** delete files unless explicitly instructed by a human maintainer.
* Follow existing code style and lint rules (`ruff` + `black`).

## 7. Large or risky changes

For migrations, API contract changes or anything touching >10 files, propose a design in `docs/proposals/` first and reference it from the daily note.

---

**Thank you!**  This lightweight process keeps context alive across computers, humans and AI models. 