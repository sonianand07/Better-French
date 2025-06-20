# LLM Research Brief – Better French Project (Version 3 Pipeline)

**Date:** 20 June 2025  
**Prepared for:** External Research Partner  
**Prepared by:** Better French Engineering Team

---

## 0  Executive summary
Better French helps foreign residents in France understand French-language news and improve their language skills.  
Our v3 AI-Engine currently uses general-purpose Large Language Models (LLMs) via the OpenRouter API to:
1. Translate French articles or snippets into **English** (and occasionally the reverse).
2. Generate **contextual word explanations** in the learner's language.
3. Produce **simplified French summaries** (B1-B2 level).

Quality is strong but variable, and the cost of proprietary frontier models is non-trivial. We seek an evidence-based recommendation on how to obtain _the best possible output quality_ **at sustainable cost**. Options include smarter prompt engineering, switching providers, or fine-tuning our own model on in-domain data.

We ask you, the researcher, to run a structured evaluation and deliver concrete guidance. This brief details:
• Current data & pipeline  • Research questions  • Candidate model families  • Potential optimisation levers  • Evaluation design  • Expected deliverables

---

## 1  Current pipeline at a glance
| Step | Purpose | Typical input | Typical output | Model today | Avg. tokens | Pain-points |
|------|---------|---------------|----------------|-------------|-------------|--------------|
| Translation | FR ⭢ EN & EN ⭢ FR | News title / 1-3 paragraphs | Fluent translation | GPT-4o (OpenRouter) | 600 | Occasional mistranslation of idioms; high cost |
| Contextual words | Identify up to 10 terms unfamiliar to B1 learner & explain | Full FR article | JSON list of term → short EN definition, FR example | GPT-4o | 800 | Sometimes misses cultural references; uneven depth |
| Summarisation | Simplify article in FR | Full FR article | ≤ 3 bullet summary, B1-B2 level | GPT-3.5-Turbo | 700 | Quality good but style uneven |
| Sentiment/metadata | Auxiliary, low-stakes | Title & lede | tags | GPT-3.5-Turbo | 100 | fine |

Configuration snippets live in `ai_engine_v3/pipeline/config.py` and Jinja prompts in `ai_engine_v3/prompts/`.

Volume: ~10 articles/hour → 240/day.  
LLM bill (May 2025): **≈ US$90 / month**.

---

## 2  Research objectives
1. **Model selection** – Identify LLM(s) that maximise quality for the three tasks above while minimising $/1k tokens.
2. **Technique selection** – Determine whether fine-tuning, retrieval augmentation, or advanced prompting offers best RoI.
3. **Data strategy** – Define what in-domain parallel/annotated corpora we would need for fine-tuning and how to source or create them legally.
4. **Evaluation** – Propose a repeatable benchmark so we can track improvements.
5. **Operational feasibility** – Consider hosting requirements, latency, licensing, privacy & vendor lock-in.

Key decision deadline: **31 July 2025** (in time for v3.2 roadmap).

---

## 3  Candidate model families to investigate
### 3.1 Proprietary APIs
| Vendor / Model | Context window | Reported strength | Price (USD / 1k tokens) | Notes |
|---------------|---------------|-------------------|-------------------------|-------|
| OpenAI GPT-4o (2024-05) | 128k | State-of-art reasoning | 5 in / 15 out | Current baseline |
| Anthropic Claude 3.5 Sonnet | 200k | Long-context, low hallucination | 3 / 15 | Promising French support |
| Google Gemini 1.5 Pro | 1M | Long docs, translation | 7 / 21 | Limited EU hosting |
| DeepL COMMIT | *NA* | Best MT FR↔EN | Pay-per-char | Only translation |
| Microsoft Phi-3-Mini (8B) | 128k | Cheap, fast | 0.06 / 0.12 | Quality TBD |

### 3.2 Open-source checkpoints (self-hosted)
| Model | Size | License | French performance | Inference cost (A100 40GB) |
|-------|------|---------|--------------------|----------------------------|
| Llama 3 70B | 70 B | Meta Llama 3 C | Very good | ~$0.0006 /1k toks |
| Mixtral 8×22B Instruct | 46 B | Apache 2.0 | Strong FR | ~$0.0004 /1k |
| Mistral Large (API) | 56 B | Closed | strong | 2 / 8 | Hosted option |
| Nous Hermes 2 | 70 B | Apache 2.0 | good | cheap |


---

## 4  Optimisation levers to explore
1. **Prompt engineering**  
   • System messages emphasising learner profile & CEFR level  
   • Use function-calling / JSON schemas to enforce structure  
   • Chained-of-thought vs. concise generation trade-offs  
2. **Retrieval-Augmented Generation (RAG)**  
   • Glossary of 🇫🇷 cultural references / administrative terms  
   • Look-up in EU-Parl / CCAligned parallel corpora for translation grounding  
3. **Fine-tuning / adapters**  
   • Supervised fine-tune on ~5k curated FR↔EN news pairs for translation  
   • LoRA adapters on Llama 3 70B for contextual-word explanations  
   • Cost: one-off ~$800 on 8×A100; inference cost unchanged  
4. **Model distillation / cascade**  
   • Cheap model first → quality filter → expensive model only on fails  
   • Could cut spend by 40-60 %.

---

## 5  Data assets we can provide
• 30 k curated French news articles (2019-2025) with titles, ledes, summaries.  
• Rolling bilingual glossary (~4 k entries).  
• Live scraped raw + processed feeds in `data/` and `ai_engine_v3/data/`.  
• User feedback logs: 👍/👎 on summaries (1 k signals).  

Gaps: High-quality human reference translations (≤ 500 today) and graded-reader style summaries.

### Must-have for fine-tuning
| Task | Required training data | Size target | Possible source |
|------|-----------------------|------------|-----------------|
| FR→EN news translation | Parallel sentences | ≥ 50k | EUParl, CCMatrix, news-crawl, custom MT + post-edit |
| Contextual word explanations | Term → simple EN def (+ FR example) | 20k | Wiki-gloss, Wiktionary, BF archives |
| Simplified summaries | FR article → 3 bullets B1 | 10k | Le Monde "Les Décodeurs", BF human edits |

---

## 6  Evaluation design
1. **Automatic metrics**  
   • Translation: BLEU, COMET-20, chrF++  
   • Summaries: ROUGE-L, BERTScore, Summac-Conv  
   • Explanations: Cosine sim vs. Wiktionary def (experimental)  
2. **Human review**  
   • 5-point Likert on fluency, adequacy, pedagogical value  
   • 20 random samples × 3 reviewers per model  
3. **Cost & latency**  
   • Wall-clock time and $/article end-to-end  
4. **Compliance checks**  
   • GDPR, license compatibility, local inference feasibility.

Deliver a **scorecard** comparing at least 6 candidate setups.

---

## 7  Deliverables & timeline
| Date | Milestone |
|------|-----------|
| 05 Jul 2025 | Draft evaluation plan & curated test set (200 items) |
| 19 Jul 2025 | Experimental results & cost analysis |
| 26 Jul 2025 | Slide deck with recommendation + hand-over call |

All code must be reproducible (Jupyter notebooks + requirements).

---

## 8  Decision framework (to be filled by researcher)
1. **If** open-source + fine-tune beats GPT-4o by ≥ 95 % quality at ≤ 30 % cost → choose OS+FT.  
2. **Else if** prompt optimisation on GPT-4o yields ≥ 10 % quality gain at ≤ same cost → stay GPT-4o.  
3. **Else** adopt hybrid cascade.

---

## 9  Open questions for you
1. What is the smallest model that meets our quality bar?  
2. Does language pair asymmetry (FR→EN vs EN→FR) matter?  
3. How stable are scores over time / vendor updates?  
4. What TCO implications of self-hosting 24/7 for 240 article/day workload?  
5. Which datasets are legally safest for commercial use?

---

## 10  Appendices
• Contextual word prompt template (`prompts/contextual_words.jinja`)  
• Sample processed article JSON  
• May 2025 LLM spend breakdown  
• Vocabulary coverage stats (top 1k missing words)  

---

_Thank you!_  
We look forward to your findings and are available on Slack `#ai-research` for questions. 