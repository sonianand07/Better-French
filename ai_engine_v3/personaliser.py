from __future__ import annotations
"""Re-rank the latest rolling_articles.json for one or more user profiles.

Usage:
    python -m ai_engine_v2.personaliser --profile profiles/u123.json --top 25
    python -m ai_engine_v2.personaliser --all-profiles profiles/*.json --top 20
"""
import argparse, glob, json, pathlib, logging
from typing import List, Dict

from .profile import UserProfile
from .pipeline.config import HIGH_RELEVANCE_KEYWORDS, MEDIUM_RELEVANCE_KEYWORDS

ROLLING_PATH = pathlib.Path(__file__).resolve().parent / "website" / "rolling_articles.json"
logger = logging.getLogger(__name__)


def load_articles() -> List[Dict]:
    if not ROLLING_PATH.exists():
        logger.error("rolling_articles.json not found – run pipeline first")
        return []
    data = json.loads(ROLLING_PATH.read_text())
    return data if isinstance(data, list) else data.get("articles", [])


def score(article: Dict, profile: UserProfile) -> float:
    txt = f"{article.get('title', '')} {article.get('summary', '')}".lower()
    score = 0.0
    for kw in profile.work_domains + profile.pain_points + profile.interests:
        if kw.lower() in txt:
            score += 3
    if profile.lives_in and profile.lives_in.lower() in txt:
        score += 2
    return score


def personalise(profile_path: pathlib.Path, top: int):
    profile = UserProfile.load(profile_path)
    arts = load_articles()
    ranked = sorted(arts, key=lambda a: score(a, profile), reverse=True)
    out = ranked[:top]
    out_dir = ROLLING_PATH.parent / "personalised"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"personal_{profile.user_id}.json"
    out_file.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    logger.info("Personalised feed for %s → %s (%d articles)", profile.user_id, out_file, len(out))


def main():
    parser = argparse.ArgumentParser(description="Personalise news feed for user profiles")
    parser.add_argument("--profile", type=str, help="Path to single profile JSON")
    parser.add_argument("--all-profiles", type=str, help="Glob pattern for multiple profiles")
    parser.add_argument("--top", type=int, default=20, help="Articles per user")
    args = parser.parse_args()

    if args.profile:
        personalise(pathlib.Path(args.profile), args.top)
    elif args.all_profiles:
        for p in glob.glob(args.all_profiles):
            personalise(pathlib.Path(p), args.top)
    else:
        parser.error("--profile or --all-profiles required")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main() 