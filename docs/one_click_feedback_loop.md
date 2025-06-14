# One-click Feedback Loop for Contextual Title Explanations

_Last updated: 14 June 2025_

## Goal
Let editors correct or enrich any token's tooltip once, then have every future AI batch automatically reproduce the fixed explanation. This provides a light-weight "memory" without retraining the model.

## Key Components
1. **Knowledge bank** – `config/manual_overrides.json`
   * Array of objects, each storing the canonical explanation for a token the AI once mishandled.
   * Example entry:
     ```json
     {
       "token": "PS",
       "correct": {
         "display_format": "**PS**",
         "explanation": "Parti socialiste – French centre-left political party",
         "cultural_note": "Often abbreviated as PS in headlines."
       }
     }
     ```

2. **Prompt enrichment in `AI-Engine.py`**
   * On each run, load `manual_overrides.json`.
   * If the headline contains any `token` from the bank, inject an additional few-shot line before the main question that demonstrates the desired treatment.
   * Adds only a handful of prompt tokens per correction.

3. **Post-generation overwrite**
   * After the model responds and passes the coverage check, loop through `contextual_title_explanations`.
   * For any `token` present in the bank, overwrite the AI output with the exact `correct` object before writing JSON to disk.

4. **One-click web UI**
   * Front-end shows a small "✏️ Edit" link in each tooltip.
   * Clicking opens a modal where the editor edits / adds a translation, CEFR, note…
   * The browser `POST`s the payload to a tiny Flask endpoint (`/api/override`), which appends or updates the entry in `manual_overrides.json`.

## Workflow
1. Editor spots a wrong or missing tooltip and clicks ✏️.
2. Front-end sends `{ token, display_format, explanation, cultural_note }` to the endpoint.
3. Endpoint merges it into the JSON bank.
4. Next time the generator runs, the fix is enforced automatically.

## Advantages
* **Zero latency** – only a small file read/write.
* **Model-agnostic** – works with any LLM.
* **Transparent** – fixes stored in plain JSON, easy to audit.

## Future Enhancements
* Add a web view to list / search existing overrides.
* Track usage stats to surface "most corrected" tokens for prompt tuning.
* Periodically prune overrides if the base model starts getting them right. 