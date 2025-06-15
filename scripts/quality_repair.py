#!/usr/bin/env python3
"""Second-pass fixer for contextual_title_explanations

This script scans Project-Better-French-Website/rolling_articles.json, finds
articles whose contextual_title_explanations are missing one or more important
multi-word names or apostrophe-words in the title, and asks the LLM only for
those missing tokens.  The goal is to avoid re-running the full AI pipeline
while still giving learners complete tool-tips.

For each token we request three learning layers so beginners, intermediates and
advanced learners all get value:
    • beginner_explanation     – a plain-English gloss of the word/phrase.
    • intermediate_explanation – a short French example sentence (<15 words).
    • advanced_explanation     – nuance / cultural or usage note (en or fr).

Usage
-----
    python3 scripts/quality_repair.py [--limit 20]

The script obeys the OpenRouter API key already configured for AI-Engine.
"""

from __future__ import annotations

import json, pathlib, argparse, importlib.util, sys, textwrap, logging, datetime, os
from typing import List, Dict, Any
from scripts.note_logger import log_task

ROOT = pathlib.Path(__file__).resolve().parent.parent
ROLLING_JSON = ROOT / 'Project-Better-French-Website' / 'rolling_articles.json'
AI_ENGINE_PATH = ROOT / 'scripts' / 'AI-Engine.py'

# ---------------------------------------------------------------------------
# Dynamic import of AI-Engine so we can reuse its helper methods & API client
# ---------------------------------------------------------------------------
_spec = importlib.util.spec_from_file_location('ai_engine', AI_ENGINE_PATH)
ai_engine = importlib.util.module_from_spec(_spec)  # type: ignore
_spec.loader.exec_module(ai_engine)  # type: ignore
Processor = ai_engine.CostOptimizedAIProcessor  # type: ignore

logger = logging.getLogger('quality_repair')
logging.basicConfig(level=logging.INFO, format='💡 %(message)s')

# ---------------------------------------------------------------------------
# Helper – expected tokens (same logic as AI-Engine, but standalone wrapper)
# ---------------------------------------------------------------------------

def expected_tokens(proc: Processor, title: str) -> set[str]:
    """Return set of tokens that must appear as whole keys."""
    import re
    tokens: set[str] = set()
    tokens.update(proc._spacy_entities(title))
    merged = proc._merge_proper_nouns(title)
    cap_pattern = r"(?:[A-Z][\w'’.-]+(?:\s+[A-Z][\w'’.-]+){1,4})"
    tokens.update(re.findall(cap_pattern, merged))
    tokens.update(re.findall(r"\b\w+'\w+", merged, flags=re.UNICODE))
    return {t.strip() for t in tokens if t.strip()}

# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def build_repair_prompt(title: str, missing: List[str]) -> str:
    tokens_list = ', '.join(missing)
    json_schema = '[\n  {\n    "original_word": "",\n    "display_format": "",\n    "explanation": ""\n  }\n]'

    return textwrap.dedent(f"""
    You are Better French assistant. We already generated contextual_title_explanations for the title:
    "{title}"

    Unfortunately some tokens were missing.  Provide ONLY the missing ones.
    Follow the same JSON shape we always use:
    {json_schema}

    Requirements:
      • One object per token listed below (no extra tokens).
      • Keep **display_format** as **OriginalWord:** plus a short French gloss.
      • Keep **explanation** concise (≤ 20 English words). No markdown fences.

    Tokens to explain: {tokens_list}
    Return ONLY the JSON array (no markdown, no prose).
    """)

# ---------------------------------------------------------------------------
# Main routine
# ---------------------------------------------------------------------------

def main(limit: int):
    if not ROLLING_JSON.exists():
        logger.error('❌ %s not found', ROLLING_JSON)
        sys.exit(1)

    data = json.loads(ROLLING_JSON.read_text())
    articles = data.get('articles', [])

    total_fixed = 0
    scanned = 0
    total_cost = 0.0
    details: List[Dict[str, Any]] = []

    proc = Processor()  # reuse API session & cost tracking

    for idx, art in enumerate(articles[:limit]):
        title = art.get('title') or art.get('original_article_title', '')
        if not title:
            continue
        scanned += 1

        expect = expected_tokens(proc, title)
        ctxt = art.get('contextual_title_explanations') or {}
        if isinstance(ctxt, dict):
            provided = set(ctxt.keys())
        elif isinstance(ctxt, list):
            provided = {d.get('original_word') for d in ctxt if isinstance(d, dict)}
        else:
            provided = set()

        missing = [t for t in expect if (" " in t or "'" in t) and t not in provided]
        if not missing:
            details.append({
                'title': title,
                'status': 'complete',
                'missing_before': 0,
                'fixed': 0
            })
            continue  # nothing to fix

        logger.info('🔧 Article %d: "%s" – repairing %d tokens', idx+1, title[:60], len(missing))
        prompt = build_repair_prompt(title, missing)

        resp = proc.call_openrouter_api(prompt, {'title': title})
        if not resp or resp[0] is None:
            logger.warning('⚠️  AI call failed, skipping')
            continue
        new_items, extra_cost = resp
        total_cost += extra_cost

        if not isinstance(new_items, list):
            logger.warning('⚠️  Unexpected AI response shape (not a list) – skipping merge for this article')
            continue

        # Merge back – preserve original structure
        if isinstance(ctxt, list):
            existing = {d.get('original_word'): d for d in ctxt if isinstance(d, dict)}
            for obj in new_items:
                existing[obj.get('original_word')] = obj
            art['contextual_title_explanations'] = list(existing.values())
        else:  # dict style or empty
            if not isinstance(ctxt, dict):
                ctxt = {}
            for obj in new_items:
                ctxt[obj.get('original_word')] = obj
            art['contextual_title_explanations'] = ctxt

        fixed_now = len(missing)
        total_fixed += fixed_now
        details.append({
            'title': title,
            'status': 'repaired',
            'missing_before': fixed_now,
            'fixed': fixed_now,
            'tokens_missing': missing,
            'tokens_added': [obj.get('original_word') for obj in new_items if isinstance(obj, dict)],
            'api_cost_usd': round(extra_cost, 6)
        })

    # -------------------------------- Summary & report --------------------------------
    repaired_articles = len([d for d in details if d['status'] == 'repaired'])
    logger.info('📊 Summary: scanned %d articles, fixed %d tokens in %d articles (cost $%.4f)',
                scanned, total_fixed, repaired_articles, total_cost)

    # Save detailed report
    logs_dir = ROOT / 'logs'
    logs_dir.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = logs_dir / f'quality_repair_report_{ts}.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({'summary': {
                      'timestamp': datetime.datetime.now().isoformat(timespec='seconds'),
                      'scanned': scanned,
                      'tokens_fixed': total_fixed,
                      'articles_repaired': repaired_articles,
                      'api_cost_usd': round(total_cost, 4)},
                    'details': details}, f, ensure_ascii=False, indent=2)
    logger.info('📝 Detailed report saved to %s', report_path)

    # Log high-level summary for humans
    log_task(
        "Quality repair run",
        f"Scanned {scanned}, fixed {total_fixed} tokens, cost ${total_cost:.4f}",
        status="done" if total_fixed else "noop",
    )

    if not total_fixed:
        logger.info('🎉 Nothing to repair – data already complete.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Repair contextual explanations')
    parser.add_argument('--limit', type=int, default=50, help='Number of articles to scan (default 50)')
    args = parser.parse_args()
    main(args.limit) 