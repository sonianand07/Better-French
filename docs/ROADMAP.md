# Better French – Roadmap (May 2025)

This document tracks **the next wave of improvements** that we will implement in the Better-French code-base and website.  
It complements—but does not replace—the main `README.md`.  Think of it as a checklist / single point of truth for anyone joining the project mid-stream.

---

## 1  Branch layout

| Branch | Purpose |
|--------|---------|
| `ui-refresh` | Purely visual & UX tweaks for the static site (no schema changes) |
| `ai-improve` | ⓐ Enhance the AI engine, ⓑ extend the data schema & storage format, ⓒ ship a one-off migration script |

> We **keep the data-model work together with the AI code** to avoid painful sequencing issues.

---

## 2  Feature buckets

### 2.1  Smarter data processing
1. **Swap/finetune LLM chain**: keep Llama-3-70B as default with Claude-Sonnet fallback.
2. **Batch token optimisation**: group shorter prompts; compress system messages.
3. **Programmatic safety checks** (toxicity, malformed JSON, hallucination guard).  
   • Add pytest coverage for edge cases.

### 2.2  Expanded article schema
The AI will start emitting new fields.  Draft v2 schema (JSON keys → type):

```jsonc
{
  "schema_version": 2,
  "id": "uuid4",
  "title": "string",
  "url": "string",
  "published_at": "ISO-8601",
  "summary": "markdown",
  "vocab": [
    { "word": "string", "definition": "string", "example": "string" }
  ],
  "difficulty": "A1 | A2 | B1 | B2 | C1 | C2",
  "tone": "neutral | opinion | satire | other",
  "keywords": ["string"],
  "audio_url": "string|null"  // reserved for future TTS
}
```

Tasks:
- [ ] Update `Article` dataclass / Pydantic model.
- [ ] Modify `ai_processor.py` to fill the new fields.
- [ ] Write migration script `scripts/migrate_v1_to_v2.py` (back-fills defaults).
- [ ] Adjust unit tests & CI.

### 2.3  UI & UX enhancements
- Surface new metadata (tone badges, CEFR difficulty chips, keyword pills).
- Add filters (difficulty dropdown, topic chips).
- Tighten typography & colour palette.
- Ensure graceful fallback if `schema_version < 2`.

### 2.4  Audio integration (coming soon)
- Generate TTS MP3 via ElevenLabs (or similar) in the pipeline.
- Upload audio to S3 → produce a public `audio_url` in the JSON.
- Add play-button component to article view.

### 2.5  Data flow & branch coordination (v1 ↔ v2)
While the schema is in transition, **both branches can build successfully** by following these rules:

| Branch | JSON it should contain | Purpose |
|--------|-----------------------|---------|
| `ui-refresh` | Latest *stable* `current_articles.json` (v1) | Let us style components without worrying about missing fields. |
| `ai-improve` | Experimental v2 JSON produced by the new pipeline | Validate schema, run CI, and publish as an artefact. |

How to test the UI with v2 early:
1. Copy the generated v2 JSON from `ai-improve` (CI artefact or local run) into `ui-refresh/data/live/current_articles.json`.
2. Commit or **git stash** (if you don't want to pollute history) and push to spawn a Netlify preview.
3. Revert once done; the real integration will happen after `ai-improve` is merged.

> The static site simply embeds the JSON at build time, so whatever file is in the branch is what the preview will display.

---

## 3  Timeline (tentative)

| Week | Milestone |
|------|-----------|
| **W-1** | Finalise v2 schema; open `ai-improve` PR with scaffolding |
| **W-2** | Migration script + CI dry-run artefacts |
| **W-3** | UI consumes v2 JSON (Netlify preview) |
| **W-4** | Merge `ai-improve` → main; release v2 live |
| **W-5** | Ship audio MVP; merge UI polish from `ui-refresh` |

Timelines are indicative—prefer working software over arbitrary dates.

---

## 4  Definition of Done
1. Netlify build passes with v2 JSON.
2. GitHub Actions pipeline succeeds end-to-end (scrape → AI → commit → Netlify).
3. Website displays new fields & audio button without console errors.
4. Unit tests ≥ 90 % coverage for new code.

---

## 5  Contributing guidelines (v2-specific)
- **Small, focused PRs**: one logical change per PR.
- Update this roadmap's checkboxes as work lands.
- Keep commit messages in the present tense ("Add tone classifier", not "Added").

### 6  Context recap & rationale for two branches
- Separation lets us ship safe, incremental UI wins while the heavier AI/data work continues in parallel.
- Rollbacks stay trivial: each PR touches only its concern (visual vs. data-model logic).
- CI remains green: UI PRs won't break when the experimental pipeline fails, and vice-versa.
- If desired, we can merge `ai-improve` *into* `ui-refresh` locally for one-off combined previews.

This recap is here so future contributors—or when the chat history is gone—understand **why** the repo has two concurrent long-lived feature branches.

Let's build! 🚀 