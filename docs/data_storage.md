# Data Storage Overview – AI-Engine v3

## Current structure

```
repo/
├── ai_engine_v3/
│   ├── data/
│   │   ├── live/          # pending queue + overflow + hashes
│   │   ├── raw_archive/   # raw RSS dumps (ignored by Git)
│   │   └── state.json     # publish counter
│   └── website/           # rolling_articles.json + backups
└── …
```

* **raw_archive/** is created at run-time by `fetch_news.py` and the scraper.
  Files live only on the runner's disk because the folder is listed in
  `.gitignore`.  That keeps the repository light.
* Nothing else in the pipeline *reads* `raw_archive/`; it is purely for
  forensic or re-processing use.

## Implications
1. The GitHub Actions runner keeps raw files for the duration of the job only.
   They disappear after each run.
2. Local developers will have a personal archive when they run the pipeline
   on their machine.

## Future idea – Supabase bucket
We may persist the raw archive in a Supabase object-storage bucket:

* Push the file from the workflow after each run (`curl` to presigned URL).
* Keep only the last *N* days locally to avoid filling disk.
* The bucket can be queried later for analytics or full re-processing.

_No code changes implemented yet – tracked as a potential enhancement._ 