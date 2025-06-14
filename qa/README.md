# QA Automation Suite for Better-French

This folder houses *all* code and assets for the automated checker bot described in `docs/ai_ui_checker_overview.md`.

Directory structure (created in later phases):

```
qa/
├── tests/           # Playwright test specs
├── scripts/         # Helper scripts to launch the server + tests locally or in CI
└── fixtures/        # Optional baseline screenshots / sample JSON
```

Phase 0 checklist (completed):

1. Added `playwright` to `requirements.txt`.
2. Placeholder `qa/` directory with this README.

Next phases will populate the sub-directories and add actual tests. 