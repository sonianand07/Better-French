# Profile-based Curation (AI-Engine v2)

## 1. Why profiles?
A front-page of 120 articles is great, but learners get more value when the feed prioritises topics relevant to **their** life and work. Profiles let us re-rank the existing AI-enhanced pool without extra LLM calls.

## 2. JSON schema (`ai_engine_v2/profile.py`)
```jsonc
{
  "user_id": "u123",
  "native_lang": "hi",
  "french_level": "B1",
  "lives_in": "Paris",
  "work_domains": ["photography", "software"],
  "pain_points": ["CAF", "loyer"],
  "interests": ["culture", "tech"]
}
```

## 3. How it works
1. **Pipeline run** writes the shared `rolling_articles.json`.
2. `python -m ai_engine_v2.personaliser --profile profiles/u123.json --top 25`
3. The personaliser scores each article:
   * +3 when a profile keyword appears in title/summary.
   * +2 when the user's city appears.
4. Highest-scoring N articles are saved as `website_demo/personalised/personal_<user>.json`.

No additional LLM calls; cost is O(users × articles) keyword checks.

## 4. Switching to Supabase later
Replace `UserProfile.load()` internals with a simple SQL `SELECT … WHERE user_id = ?`. No other code changes.

## 5. Quick start
```
# create a profile
python - <<'PY'
from ai_engine_v2.profile import UserProfile
UserProfile(
    user_id="demo",
    native_lang="en",
    lives_in="Lyon",
    work_domains=["software", "AI"],
    pain_points=["impôts"],
    interests=["startup"]
).save()
PY

# run pipeline then personalise
OPENROUTER_API_KEY=sk-... python -m ai_engine_v2.pipeline.runner --limit 10
python -m ai_engine_v2.personaliser --profile profiles/demo.json --top 20
```
Open `website_demo/index.html` and tweak the fetch path to load `personalised/personal_demo.json` for a quick local preview. 