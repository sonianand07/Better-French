#!/usr/bin/env python3
"""
AI Engine v5 - Autonomous Scraper
Handles minimal, fast scraping with LLM-powered article selection.
CRITICAL: Uses separate API key to ensure 24/7 reliability.
FIXED: Now uses V3's proven scoring system instead of generic LLM prompt.
"""

import json
import requests
import os
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone, timedelta
import hashlib
import asyncio
import aiohttp
import feedparser
import logging
from dataclasses import dataclass, asdict

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.rss_sources import RSS_SOURCES

logger = logging.getLogger(__name__)

# Import V3's proven scoring system
HIGH_RELEVANCE_KEYWORDS = [
    # Visas & immigration
    "visa", "titre de séjour", "carte de séjour", "naturalisation", "immigration", "étranger",
    # Work & salary
    "smic", "salaire", "cotisations", "travail", "code du travail", "congé", "prélèvement à la source",
    # Housing & cost of living
    "loyer", "caf", "APL", "logement", "bail", "pouvoir d'achat",
    # Transport strikes / SNCF / RATP
    "grève", "SNCF", "RATP", "trafic", "panne",
    # Health & social security
    "sécurité sociale", "ameli", "mutuelle", "assurance maladie",
    # Civic & daily-life topics that matter to any resident of France
    "france", "politique", "économie", "justice", "santé", "écologie",
    # Day-to-day admin & services
    "assurance habitation", "ram", "carte vitale", "taxe d'habitation",
    "mutuelle étudiante", "doctolib", "carte navigo",
]

MEDIUM_RELEVANCE_KEYWORDS = [
    "retraite", "impôts", "URSSAF", "CAF", "énergie", "inflation", "prix", "taxe foncière",
    "olympiques", "jeux olympiques", "élections", "météo", "météo-extrême",
    "grève nationale", "canicule", "tempête", "sécheresse",
]

CURATOR_WEIGHTS = {
    "relevance": 1.2,
    "practical": 1.0,
    "newsworthiness": 0.8,
}

@dataclass
class ArticleData:
    title: str
    link: str
    summary: str
    published: str
    source: str
    hash_id: str
    raw_content: str = ""
    # V3-style scoring
    relevance_score: float = 0.0
    practical_score: float = 0.0
    newsworthiness_score: float = 0.0
    total_score: float = 0.0

@dataclass  
class UserProfile:
    """Profile data for personalized article selection"""
    user_id: str = "default"
    native_lang: str = "en"
    french_level: str = "B1"
    lives_in: str = ""
    work_domains: List[str] = None
    pain_points: List[str] = None
    interests: List[str] = None
    
    def __post_init__(self):
        if self.work_domains is None:
            self.work_domains = []
        if self.pain_points is None:
            self.pain_points = []
        if self.interests is None:
            self.interests = []
    
    @classmethod
    def from_json(cls, profile_data: Dict) -> 'UserProfile':
        return cls(**profile_data)
    
    def get_keywords(self) -> Set[str]:
        """Get all profile keywords for relevance scoring"""
        keywords = set()
        keywords.update(kw.lower() for kw in self.work_domains)
        keywords.update(kw.lower() for kw in self.pain_points)
        keywords.update(kw.lower() for kw in self.interests)
        if self.lives_in:
            keywords.add(self.lives_in.lower())
        return keywords

class AutonomousScraper:
    """Rony - The autonomous French news scraper
    
    Scrapes 31 RSS sources and uses V3's PROVEN scoring system
    combined with LLM intelligence for the best of both worlds.
    """
    
    def __init__(self, api_key: str, profile: Optional[UserProfile] = None):
        self.api_key = api_key
        self.profile = profile or UserProfile()  # Default profile if none provided
        self.session: Optional[aiohttp.ClientSession] = None
        
        # V3's proven keyword sets
        self.high_kw = set(HIGH_RELEVANCE_KEYWORDS)
        self.medium_kw = set(MEDIUM_RELEVANCE_KEYWORDS)
        self.profile_kw = set()
        if profile:
            self.profile_kw.update({w.lower() for w in profile.work_domains})
            self.profile_kw.update({w.lower() for w in profile.pain_points})
            self.profile_kw.update({w.lower() for w in profile.interests})
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _generate_hash(self, title: str, link: str) -> str:
        """Generate unique hash for article deduplication"""
        content = f"{title}{link}".encode('utf-8')
        return hashlib.md5(content).hexdigest()[:12]
    
    def _score_relevance(self, text: str) -> float:
        """Score relevance using V3's proven keyword system"""
        txt = text.lower()
        
        # High relevance keywords (+9.0)
        if any(kw in txt for kw in self.high_kw):
            return 9.0
        
        # Medium relevance keywords (+7.0)
        if any(kw in txt for kw in self.medium_kw):
            return 7.0
        
        # France-wide catch-all so big national topics aren't missed (+7.0)
        if "france" in txt or "français" in txt:
            return 7.0
        
        # Profile-specific keywords (+6.0)
        if self.profile_kw and any(kw in txt for kw in self.profile_kw):
            return 6.0
        
        return 4.0  # Base score
    
    def _score_practical(self, text: str) -> float:
        """Score practical value (simplified version of V3's SpaCy scoring)"""
        txt = text.lower()
        score = 0
        
        # Look for practical indicators
        money_indicators = ['€', 'euros', 'prix', 'coût', 'budget', 'salaire', 'smic']
        if any(indicator in txt for indicator in money_indicators):
            score += 3
        
        date_indicators = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                          'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
                          '2025', '2024', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi']
        if any(indicator in txt for indicator in date_indicators):
            score += 2
        
        percent_indicators = ['%', 'pourcent', 'pour cent', 'hausse', 'baisse']
        if any(indicator in txt for indicator in percent_indicators):
            score += 1
        
        org_indicators = ['gouvernement', 'ministère', 'préfecture', 'mairie', 'CAF', 'SNCF']
        if any(indicator in txt for indicator in org_indicators):
            score += 1
        
        return min(score, 9)
    
    def _score_newsworthiness(self, article: ArticleData) -> float:
        """Score newsworthiness using V3's method"""
        # Crude heuristic: longer summary -> higher (like V3)
        length = len(article.summary.split()) if article.summary else 0
        return 6 + min(length / 100, 4)
    
    def _calculate_v3_score(self, article: ArticleData) -> ArticleData:
        """Calculate V3-style scores for article"""
        full_text = f"{article.title} {article.summary}"
        
        relevance = self._score_relevance(full_text)
        practical = self._score_practical(full_text)
        newsworthiness = self._score_newsworthiness(article)
        
        # Apply V3's weights
        total = (relevance * CURATOR_WEIGHTS["relevance"] + 
                practical * CURATOR_WEIGHTS["practical"] + 
                newsworthiness * CURATOR_WEIGHTS["newsworthiness"])
        
        article.relevance_score = relevance
        article.practical_score = practical
        article.newsworthiness_score = newsworthiness
        article.total_score = total
        
        return article

    async def _fetch_rss_feed(self, source_name: str, url: str) -> List[ArticleData]:
        """Fetch and parse a single RSS feed"""
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {source_name}: HTTP {response.status}")
                    return []
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                articles = []
                for entry in feed.entries[:10]:  # Limit per source
                    article = ArticleData(
                        title=entry.get('title', ''),
                        link=entry.get('link', ''),
                        summary=entry.get('summary', entry.get('description', '')),
                        published=entry.get('published', ''),
                        source=source_name,
                        hash_id=self._generate_hash(entry.get('title', ''), entry.get('link', ''))
                    )
                    # Calculate V3-style scores
                    article = self._calculate_v3_score(article)
                    articles.append(article)
                
                logger.info(f"Fetched {len(articles)} articles from {source_name}")
                return articles
                
        except Exception as e:
            logger.error(f"Error fetching {source_name}: {e}")
            return []
    
    async def scrape_all_sources(self) -> List[ArticleData]:
        """Scrape all RSS sources concurrently"""
        logger.info(f"Rony starting scrape of {len(RSS_SOURCES)} sources...")
        
        tasks = []
        for source_name, url in RSS_SOURCES.items():
            task = self._fetch_rss_feed(source_name, url)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Feed fetch failed: {result}")
        
        # Deduplicate by hash_id
        seen_hashes = set()
        unique_articles = []
        for article in all_articles:
            if article.hash_id not in seen_hashes:
                seen_hashes.add(article.hash_id)
                unique_articles.append(article)
        
        logger.info(f"Rony collected {len(unique_articles)} unique articles from {len(RSS_SOURCES)} sources")
        return unique_articles
    
    async def _select_best_articles(self, articles: List[ArticleData]) -> List[ArticleData]:
        """Select best articles using V3's proven system + LLM intelligence"""
        
        if not articles:
            return []
        
        logger.info("🎯 Applying V3's proven scoring system...")
        
        # Step 1: Apply V3's threshold filter (≥10 total score like V3)
        MIN_SCORE_THRESHOLD = 10.0  # Same as V3's CuratorV2
        approved = [a for a in articles if a.total_score >= MIN_SCORE_THRESHOLD]
        logger.info(f"V3 scoring: {len(approved)}/{len(articles)} articles passed threshold (≥{MIN_SCORE_THRESHOLD})")
        
        if not approved:
            logger.warning("No articles passed V3 quality threshold - lowering standards")
            # Fallback: lower threshold
            approved = [a for a in articles if a.total_score >= 8.0]
        
        # Step 2: Sort by V3 total score
        approved.sort(key=lambda x: x.total_score, reverse=True)
        
        # Step 3: Apply V3's global event capping (like CuratorV2)
        # For now, we'll just take top articles by score
        
        # Step 4: LLM final selection for diversity and profile fit
        if len(approved) > 10:
            logger.info("🤖 Using LLM for final diversity selection from V3-approved articles...")
            
            # Prepare top 20 V3-approved articles for LLM review
            top_candidates = approved[:min(20, len(approved))]
            
            profile_context = f"""
USER PROFILE:
- French Level: {self.profile.french_level}
- Lives in: {self.profile.lives_in or 'France'}
- Work Domains: {', '.join(self.profile.work_domains) if self.profile.work_domains else 'General'}
- Pain Points: {', '.join(self.profile.pain_points) if self.profile.pain_points else 'None specified'}
- Interests: {', '.join(self.profile.interests) if self.profile.interests else 'General news'}
            """
            
            # Prepare article summaries for LLM
            article_summaries = []
            for i, article in enumerate(top_candidates):
                summary = f"{i+1}. {article.title}\n   Source: {article.source}\n   V3 Score: {article.total_score:.1f}\n   Summary: {article.summary[:150]}..."
                article_summaries.append(summary)
            
            prompt = f"""You are selecting the FINAL 10 articles from {len(top_candidates)} that already passed V3's proven quality scoring system.

{profile_context}

These articles all scored ≥{MIN_SCORE_THRESHOLD} on V3's proven relevance system. Your job is to select the 10 most diverse and profile-relevant articles.

Focus on:
1. Topic diversity (avoid 5 articles about same event)
2. Profile relevance for this specific user
3. Mix of importance levels (some breaking news, some practical advice)
4. Geographic relevance ({self.profile.lives_in or 'France'})

PRE-SCORED ARTICLES:
{chr(10).join(article_summaries)}

Respond with ONLY the numbers of the 10 best articles for this user, separated by commas.
Example: 1,3,7,12,15,18,22,25,28,30"""

            try:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'model': 'google/gemini-2.0-flash-exp:free',
                    'messages': [
                        {
                            'role': 'user', 
                            'content': prompt
                        }
                    ],
                    'max_tokens': 50,
                    'temperature': 0.3
                }
                
                async with self.session.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        logger.error(f"LLM diversity selection failed: {response.status}")
                        # Fallback: take top 10 by V3 score
                        return approved[:10]
                    
                    result = await response.json()
                    selected_text = result['choices'][0]['message']['content'].strip()
                    
                    # Parse selected indices
                    try:
                        selected_indices = [int(x.strip()) - 1 for x in selected_text.split(',')]
                        selected_articles = [top_candidates[i] for i in selected_indices if 0 <= i < len(top_candidates)]
                        
                        if len(selected_articles) >= 8:  # Accept if we got most articles
                            logger.info(f"🎯 V3+LLM selection: {len(selected_articles)} articles (V3 scoring + LLM diversity)")
                            return selected_articles[:10]
                        else:
                            logger.warning("LLM selection returned too few articles - using V3 top 10")
                            return approved[:10]
                        
                    except (ValueError, IndexError) as e:
                        logger.error(f"Failed to parse LLM selection: {e}")
                        return approved[:10]
                        
            except Exception as e:
                logger.error(f"LLM diversity selection failed: {e}")
                return approved[:10]  # Fallback to V3 scoring
        
        else:
            # If we have ≤10 articles, just return them all
            logger.info(f"🎯 V3 scoring selected {len(approved)} articles (all passed quality threshold)")
            return approved
    
    async def run_autonomous_cycle(self) -> Dict:
        """Complete autonomous scraping and selection cycle"""
        start_time = datetime.now()
        
        # Step 1: Scrape all sources
        all_articles = await self.scrape_all_sources()
        
        if not all_articles:
            logger.warning("No articles collected!")
            return {
                "timestamp": start_time.isoformat(),
                "articles_collected": 0,
                "articles_selected": 0,
                "selected_articles": [],
                "profile_used": asdict(self.profile),
                "v3_scoring_applied": True,
                "selection_method": "V3 proven system + LLM diversity"
            }
        
        # Step 2: Intelligent selection using V3's proven system + LLM
        selected_articles = await self._select_best_articles(all_articles)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate quality metrics
        if selected_articles:
            avg_v3_score = sum(a.total_score for a in selected_articles) / len(selected_articles)
            min_v3_score = min(a.total_score for a in selected_articles)
            max_v3_score = max(a.total_score for a in selected_articles)
        else:
            avg_v3_score = min_v3_score = max_v3_score = 0.0
        
        logger.info(f"🎉 Rony completed autonomous cycle in {duration:.1f}s")
        logger.info(f"   📊 Selection: {len(all_articles)} → {len(selected_articles)} articles")
        logger.info(f"   🎯 V3 Quality: avg={avg_v3_score:.1f}, min={min_v3_score:.1f}, max={max_v3_score:.1f}")
        logger.info(f"   ✅ PROVEN V3 scoring system preserved!")
        
        return {
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "articles_collected": len(all_articles),
            "articles_selected": len(selected_articles),
            "selected_articles": [asdict(article) for article in selected_articles],
            "profile_used": asdict(self.profile),
            "sources_scraped": list(RSS_SOURCES.keys()),
            "v3_scoring_applied": True,
            "selection_method": "V3 proven system + LLM diversity",
            "quality_metrics": {
                "avg_v3_score": avg_v3_score,
                "min_v3_score": min_v3_score,
                "max_v3_score": max_v3_score,
                "threshold_used": 10.0
            }
        }

# Convenience function for single-use
async def run_autonomous_scraper(api_key: str, profile_data: Optional[Dict] = None) -> Dict:
    """Run Rony's autonomous scraping cycle with V3's proven scoring"""
    profile = None
    if profile_data:
        profile = UserProfile.from_json(profile_data)
    
    async with AutonomousScraper(api_key, profile) as scraper:
        return await scraper.run_autonomous_cycle() 