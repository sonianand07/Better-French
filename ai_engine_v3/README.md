# Better French – AI-Engine v3

This folder is a **frozen copy of v2** that will evolve into the next-gen pipeline.
The goals are:

* Deliver at most **50 high-quality headlines per day**
* Guarantee every published headline contains contextual glossary words
* Balance the feed across work-domain, world-affairs and France-general buckets
* Rely on an LLM for nuanced relevance scoring while keeping costs predictable

---
## 1.  Two-stage pipeline

| Stage | Script | Frequency | Cost | Responsibility |
|-------|--------|-----------|------|----------------|
| Fetch | `scripts/fetch_news.py` | 30 min |  free | scrape RSS feeds → save raw JSON under `data/raw_archive/` |
| Qualify | `scripts/qualify_news.py` | 1–2 h |  LLM × headlines that passed rule filter | ❶ curate with rules ❷ call LLM for relevance ❸ cap to 50/day ❹ run full Processor ❺ publish to website |

### Daily cap logic
A small `state.json` keeps two fields:
* `date` – ISO date of last run.
* `published_today` – counter reset at midnight.

If the counter ≥ 50 the qualifier exits early.

---
## 2.  Relevance scoring

`ai_engine_v3/relevance_llm.py` sends one short prompt per headline to **Claude 3.5 Sonnet** and returns a 0-10 score.  Final score = 60 % rule-score + 40 % LLM score.

Prompt template (truncated):
> "You are ranking news for an expat professional in France (tech industry, energy policy, world events)…Rate 0-10."

---
## 3.  Bucket balancing

After sorting by blended score the qualifier pulls:
* ~10 work-domain stories (tech / energy keywords)
* ~10 major world-affairs stories (`global_event=True`)
* Remaining slots go to France general interest.

If a bucket is short its unused slots roll over.

---
## 4.  Updated ordering

`ai_engine_v3/storage.py` now sorts by `original_article_published_date` (fallback `processed_at`) so the site always shows the newest real news first.

---
## 5.  New French sources added

`pipeline/config.py` gains these RSS feeds:
* Le Figaro
* Les Échos
* L'Obs
* France Info
* AFP (general)

---
## 6.  Testing

• `qa/local/check_contextual_words_v3.py` – smoke test downloads the live rolling feed and checks glossaries, coverage, visible matches and ordering.

• `tests/ai_engine_v3/test_qualifier.py` – mocks the LLM and asserts that at most 50 items are selected and that the daily counter is respected.

---
## 7.  Running locally

```bash
# fetch latest raw headlines
PYTHONPATH=. python3 ai_engine_v3/scripts/fetch_news.py

# qualify + publish (respects daily cap)
PYTHONPATH=. python3 ai_engine_v3/scripts/qualify_news.py

# quick smoke-test against produced feed
PYTHONPATH=. python3 qa/local/check_contextual_words_v3.py --path ai_engine_v3/website/rolling_articles.json
```

---
## 8.  Roadmap / TODO

- [ ] Implement bucket-balancing logic in `qualify_news.py`
- [ ] Add the new RSS feeds to `pipeline/config.py`
- [ ] Write unit tests and smoke test duplicates for v3
- [ ] Set up cron / GitHub Actions schedules (fetch @ */30min, qualify @ */2h)
- [ ] Gradually switch Netlify to point at `ai_engine_v3/website/` 