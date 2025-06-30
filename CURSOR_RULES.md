# Cursor Assistant Master Rulebook

> **Purpose**: One canonical reference for *both* humans and AI assistants (LLMs) working inside the Cursor IDE on this repository.  It fully supersedes the old `AI_CONTRIBUTION_GUIDE.md` and the previous lightweight `CURSOR_RULES.md` so there is no split-brain confusion.
>
> If a rule here ever conflicts with another document, **this file wins**.

---

## 0. Golden principles

1. Protect the main branch and production data.  
2. Preserve context by writing notes & docs alongside code.  
3. Favour clarity over cleverness; future maintainers include LLMs with zero prior context.

---

## 1. Session workflow for AI assistants

1. **Read before you write**  
   • Open the latest daily note in `docs/daily_notes/` (named `YYYY-MM-DD.md`).  
   • Skim any architecture docs linked from that note.  
   • Only then begin coding or documentation changes.
2. **Daily engineering log**  
   • At the end of every working session create *or* update today's note using the template.  
   • Must include: accomplishments, pain-points, next actions, file-change log.
3. **Use the template**  
   Copy `docs/daily_notes/template.md` → current date.  Keep the built-in **Task tracker** table (`✅ Done`, `🚧 In Progress`, `❌ Pending`, `🛑 Blocked`, `🗑️ Dropped`).  Only mark `Done` when effects are observable (CI green, feature live).

---

## 2. Commit policy

* Code **and** notes belong in the *same commit*. No PR should modify code without an accompanying daily note update.
* If a session touches *no* code but only research/analysis it **still** produces a note.
* Pre-commit hook (`scripts/check_daily_note.py`) verifies a note for *today* exists and has a "File change log". Enable via:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
```

* **Path refactor safety:** If you rename or move directories/files, grep the `.github/workflows/` folder for hard-coded paths (e.g. `git add old_path`) and update them. Add a tiny CI assertion or `set -e` so a missing path causes the workflow to fail rather than silently skip staging.

---

## 3. Backlog maintenance (docs/future_features.md)

The *Future Features Backlog* is the single source-of-truth for product-level ideas.

1. **Row schema** – Exactly four columns: `ID`, `Feature`, `Brief`, `Status`.  Use `<br/>` for line breaks inside *Brief* cells.  Allowed statuses: `❌ Pending`, `🚧 In Progress`, `✅ Done`, `🛑 Blocked`.
2. **Detailed briefs** – Every ID must have a matching `#### F-XXX` heading under **Detailed briefs** with WHAT / WHY / HOW.
3. **Lifecycle** – When a feature ships, move its row to the *Done* table and archive/remove its brief.
4. **Formatting guardrails** – No blank lines inside the table.  Keep the `|----|` separator exactly three dashes wide.
5. **Hidden AI comment** – File begins with an HTML comment repeating these rules (already in place).  Do **not** delete it.
6. **Human approval** – Any PR touching `future_features.md` requires at least one human review.
7. **Linter** – If `scripts/check_future_features.py` exists, run it in pre-commit & CI; commits fail on schema or formatting violations.

---

## 4. Large or risky changes

For migrations, API contract changes or anything touching >10 files, first create a design doc in `docs/proposals/` and reference it from the daily note.

---

## 5. Repository hygiene

* Do **not** delete files unless explicitly instructed by a human maintainer.  
* Follow existing code style & lint rules (`ruff` + `black`).

---

## 6. Runtime safety rules (live during a Cursor session)

1. **Pending edits check** – After proposing a code change (`edit_file`), pause and wait for the user to accept/reject before running follow-up automation, QA or scripts.
2. **Confirmation before execution** – Any long-running or write-heavy script must be explicitly green-lit by the user after latest edits.
3. **Branch safety** – Never mutate `main`; work on the current feature branch unless told otherwise.
4. **Verbose status** – When waiting for approval say: "Awaiting approval of the previous edit – no scripts executed."

---

## 7. Tool-usage & formatting guidelines

### 7.1 Code citations
Use the strict format:

```text
12:15:path/to/file.py
// ... existing code ...
```

(No other formats are allowed.)

### 7.2 `edit_file` usage
* Only include the modified lines; represent omissions with `// ... existing code ...`.
* If the automatic apply model mis-produces the diff, call `reapply` once.
* Stop after three linter-fix attempts and ask the user.

### 7.3 Terminal commands
* Prefer non-interactive flags (`--yes`, `--force`, etc.).
* Pipe pagers through `| cat`.
* Background long-running jobs via `is_background: true`.

### 7.4 External info
* Bias toward semantic search / repo inspection rather than asking the user.

---

## 8. Glossary

* **Daily note** – Markdown file in `docs/daily_notes/YYYY-MM-DD.md` recording today's work.  
* **Backlog** – `docs/future_features.md`, row of planned feature with brief + status.  
* **WHAT / WHY / HOW** – Mini-spec format used in detailed briefs.

---

## 9. Change management for this rulebook

* Any modification to **this** file requires a human code-owner review.  
* Version the history through Git; do not force-push rewrites without strong justification.

---

## 10. Paris Time Reference

* **ALWAYS use Paris time (CET/CEST)** when communicating timestamps, schedules, or time-based information
* User is located in Paris - all time references should be Paris-synchronized
* When analyzing workflows, Rony runs, or any time-sensitive data, convert to Paris time for clarity

---

**End of rulebook** 