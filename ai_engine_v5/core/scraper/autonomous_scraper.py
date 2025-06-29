#!/usr/bin/env python3
"""
AI Engine v5 - Autonomous Scraper
Handles minimal, fast scraping with LLM-powered article selection.
CRITICAL: Uses separate API key to ensure 24/7 reliability.
FIXED: Now uses V3's proven scoring system instead of generic LLM prompt.
IMPROVED: Added robust error handling, retry logic, and detailed logging.
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
import time
import random

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.rss_sources import RSS_SOURCES

# Configure logging for better debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
    
    WORLD'S BEST SCRAPER - Enhanced with:
    - V3's PROVEN scoring system
    - Robust error handling & retry logic
    - Comprehensive logging for debugging
    - Fallback mechanisms for reliability
    """
    
    def __init__(self, api_key: str, profile: Optional[UserProfile] = None):
        self.api_key = api_key
        self.profile = profile or UserProfile()  # Default profile if none provided
        self.session: Optional[aiohttp.ClientSession] = None
        self.scraping_stats = {
            'sources_attempted': 0,
            'sources_successful': 0,
            'sources_failed': 0,
            'total_articles_scraped': 0,
            'failed_sources': []
        }
        
        # V3's proven keyword sets
        self.high_kw = set(HIGH_RELEVANCE_KEYWORDS)
        self.medium_kw = set(MEDIUM_RELEVANCE_KEYWORDS)
        self.profile_kw = set()
        if profile:
            self.profile_kw.update({w.lower() for w in profile.work_domains})
            self.profile_kw.update({w.lower() for w in profile.pain_points})
            self.profile_kw.update({w.lower() for w in profile.interests})
        
        logger.info(f"🤖 Rony initialized with {len(self.high_kw)} high-relevance + {len(self.medium_kw)} medium-relevance keywords")
        logger.info(f"👤 Profile: {len(self.profile_kw)} custom keywords, level={self.profile.french_level}")
        
    async def __aenter__(self):
        # Configure session with proper headers and timeouts
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=3)
        timeout = aiohttp.ClientTimeout(total=45, connect=15)
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; RonyBot/1.0; +https://betterfrench.news)',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8'
        }
        self.session = aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout,
            headers=headers
        )
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
        high_matches = [kw for kw in self.high_kw if kw in txt]
        if high_matches:
            logger.debug(f"High relevance match: {high_matches[:3]}")
            return 9.0
        
        # Medium relevance keywords (+7.0)
        medium_matches = [kw for kw in self.medium_kw if kw in txt]
        if medium_matches:
            logger.debug(f"Medium relevance match: {medium_matches[:3]}")
            return 7.0
        
        # France-wide catch-all so big national topics aren't missed (+7.0)
        if "france" in txt or "français" in txt:
            logger.debug("France-wide relevance match")
            return 7.0
        
        # Profile-specific keywords (+6.0)
        profile_matches = [kw for kw in self.profile_kw if kw in txt]
        if profile_matches:
            logger.debug(f"Profile relevance match: {profile_matches[:3]}")
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
        
        logger.debug(f"V3 scoring - {article.title[:50]}... = R:{relevance:.1f} P:{practical:.1f} N:{newsworthiness:.1f} TOTAL:{total:.1f}")
        
        return article
    
    async def _fetch_rss_feed(self, source_name: str, url: str, max_retries: int = 3) -> List[ArticleData]:
        """Fetch and parse a single RSS feed with retry logic"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Add jitter to prevent thundering herd
                if attempt > 0:
                    await asyncio.sleep(random.uniform(1, 3) * attempt)
                
                logger.debug(f"Fetching {source_name} (attempt {attempt + 1}/{max_retries})")
                
                async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 429:  # Rate limited
                        logger.warning(f"{source_name}: Rate limited, waiting...")
                        await asyncio.sleep(random.uniform(5, 10))
                        continue
                    elif response.status == 403:
                        logger.warning(f"{source_name}: Blocked (403) - may need different user agent")
                        last_error = f"HTTP 403 (blocked)"
                        continue
                    elif response.status != 200:
                        logger.warning(f"{source_name}: HTTP {response.status}")
                        last_error = f"HTTP {response.status}"
                        continue
                    
                    content = await response.text()
                    feed = feedparser.parse(content)
                    
                    if not feed.entries:
                        logger.warning(f"{source_name}: No entries found in feed")
                        last_error = "No entries found"
                        continue
                    
                    articles = []
                    for entry in feed.entries[:15]:  # Increased limit per source
                        try:
                            article = ArticleData(
                                title=entry.get('title', '').strip(),
                                link=entry.get('link', '').strip(),
                                summary=entry.get('summary', entry.get('description', '')).strip(),
                                published=entry.get('published', ''),
                                source=source_name,
                                hash_id=self._generate_hash(entry.get('title', ''), entry.get('link', ''))
                            )
                            
                            # Skip articles with missing critical data
                            if not article.title or not article.link:
                                continue
                                
                            # Calculate V3-style scores
                            article = self._calculate_v3_score(article)
                            articles.append(article)
                            
                        except Exception as e:
                            logger.debug(f"Error processing entry from {source_name}: {e}")
                            continue
                    
                    self.scraping_stats['sources_successful'] += 1
                    self.scraping_stats['total_articles_scraped'] += len(articles)
                    logger.info(f"✅ {source_name}: {len(articles)} articles (avg score: {sum(a.total_score for a in articles)/len(articles):.1f})")
                    return articles
                    
            except asyncio.TimeoutError:
                last_error = "Timeout"
                logger.warning(f"{source_name}: Timeout on attempt {attempt + 1}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"{source_name}: Error on attempt {attempt + 1}: {e}")
        
        # All retries failed
        self.scraping_stats['sources_failed'] += 1
        self.scraping_stats['failed_sources'].append({'source': source_name, 'error': last_error})
        logger.error(f"❌ {source_name}: Failed after {max_retries} attempts - {last_error}")
        return []
    
    async def scrape_all_sources(self) -> List[ArticleData]:
        """Scrape all RSS sources concurrently with improved error handling"""
        logger.info(f"🚀 Rony starting intelligent scrape of {len(RSS_SOURCES)} sources...")
        self.scraping_stats['sources_attempted'] = len(RSS_SOURCES)
        
        # Create tasks with semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(8)  # Max 8 concurrent requests
        
        async def fetch_with_semaphore(source_name, url):
            async with semaphore:
                return await self._fetch_rss_feed(source_name, url)
        
        tasks = [fetch_with_semaphore(name, url) for name, url in RSS_SOURCES.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Unexpected error in feed fetch: {result}")
        
        # Deduplicate by hash_id
        seen_hashes = set()
        unique_articles = []
        for article in all_articles:
            if article.hash_id not in seen_hashes:
                seen_hashes.add(article.hash_id)
                unique_articles.append(article)
        
        success_rate = (self.scraping_stats['sources_successful'] / self.scraping_stats['sources_attempted']) * 100
        logger.info(f"📊 Scraping complete: {len(unique_articles)} unique articles from {self.scraping_stats['sources_successful']}/{self.scraping_stats['sources_attempted']} sources ({success_rate:.1f}% success)")
        
        if self.scraping_stats['failed_sources']:
            logger.warning(f"⚠️  Failed sources: {[s['source'] for s in self.scraping_stats['failed_sources']]}")
        
        return unique_articles
    
    async def _llm_request_with_retry(self, payload: Dict, max_retries: int = 3) -> Optional[Dict]:
        """Make LLM request with exponential backoff retry"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        for attempt in range(max_retries):
            try:
                # Exponential backoff with jitter
                if attempt > 0:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retrying LLM request in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                
                async with self.session.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=90)  # Increased timeout
                ) as response:
                    
                    if response.status == 429:  # Rate limited
                        logger.warning(f"LLM rate limited, attempt {attempt + 1}/{max_retries}")
                        continue
                    elif response.status != 200:
                        logger.error(f"LLM request failed: HTTP {response.status}")
                        continue
                    
                    result = await response.json()
                    logger.info("✅ LLM selection successful")
                    return result
                    
            except asyncio.TimeoutError:
                logger.warning(f"LLM request timeout, attempt {attempt + 1}/{max_retries}")
            except Exception as e:
                logger.error(f"LLM request error, attempt {attempt + 1}/{max_retries}: {e}")
        
        logger.error("❌ LLM selection failed after all retries")
        return None

    async def _select_best_articles(self, articles: List[ArticleData]) -> List[ArticleData]:
        """Select best articles using V3's proven system + LLM intelligence"""
        
        if not articles:
            logger.warning("No articles to select from!")
            return []
        
        logger.info("🎯 Applying V3's proven scoring system...")
        
        # Step 1: Apply V3's threshold filter (≥10 total score like V3)
        MIN_SCORE_THRESHOLD = 10.0  # Same as V3's CuratorV2
        approved = [a for a in articles if a.total_score >= MIN_SCORE_THRESHOLD]
        logger.info(f"📊 V3 scoring: {len(approved)}/{len(articles)} articles passed threshold (≥{MIN_SCORE_THRESHOLD})")
        
        if not approved:
            logger.warning("⚠️  No articles passed V3 quality threshold - lowering standards...")
            # Fallback: lower threshold
            approved = [a for a in articles if a.total_score >= 8.0]
            logger.info(f"📊 Fallback threshold: {len(approved)} articles passed (≥8.0)")
        
        if not approved:
            logger.error("❌ No articles passed even lowered threshold - taking top 10 by score")
            approved = sorted(articles, key=lambda x: x.total_score, reverse=True)[:10]
        
        # Step 2: Sort by V3 total score
        approved.sort(key=lambda x: x.total_score, reverse=True)
        
        # Step 3: Quality metrics
        if approved:
            avg_score = sum(a.total_score for a in approved) / len(approved)
            min_score = min(a.total_score for a in approved)
            max_score = max(a.total_score for a in approved)
            logger.info(f"🎯 V3 Quality metrics: avg={avg_score:.1f}, min={min_score:.1f}, max={max_score:.1f}")
        
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

            payload = {
                'model': 'google/gemini-2.0-flash-exp:free',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 100,
                'temperature': 0.3
            }
            
            llm_result = await self._llm_request_with_retry(payload)
            
            if llm_result:
                try:
                    selected_text = llm_result['choices'][0]['message']['content'].strip()
                    
                    # Parse selected indices
                    selected_indices = [int(x.strip()) - 1 for x in selected_text.split(',')]
                    selected_articles = [top_candidates[i] for i in selected_indices if 0 <= i < len(top_candidates)]
                    
                    if len(selected_articles) >= 8:  # Accept if we got most articles
                        logger.info(f"🎯 V3+LLM selection: {len(selected_articles)} articles (V3 scoring + LLM diversity)")
                        return selected_articles[:10]
                    else:
                        logger.warning("⚠️  LLM selection returned too few articles - using V3 top 10")
                        return approved[:10]
                    
                except (ValueError, IndexError) as e:
                    logger.error(f"Failed to parse LLM selection: {e}")
                    return approved[:10]
            else:
                logger.warning("LLM diversity selection failed - using V3 top 10")
                return approved[:10]  # Fallback to V3 scoring
        
        else:
            # If we have ≤10 articles, just return them all
            logger.info(f"🎯 V3 scoring selected {len(approved)} articles (all passed quality threshold)")
            return approved
    
    async def run_autonomous_cycle(self) -> Dict:
        """Complete autonomous scraping and selection cycle"""
        start_time = datetime.now()
        logger.info("🚀 Starting Rony's autonomous cycle...")
        
        # Step 1: Scrape all sources
        all_articles = await self.scrape_all_sources()
        
        if not all_articles:
            logger.error("❌ No articles collected!")
            return {
                "timestamp": start_time.isoformat(),
                "articles_collected": 0,
                "articles_selected": 0,
                "selected_articles": [],
                "profile_used": asdict(self.profile),
                "v3_scoring_applied": True,
                "selection_method": "V3 proven system + LLM diversity",
                "scraping_stats": self.scraping_stats
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
        
        # Step 3: INTELLIGENT DATA PERSISTENCE - No overwrites, smart merging
        current_run_data = {
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
            "articles_collected": len(all_articles),
            "articles_selected": len(selected_articles),
            "selected_articles": [asdict(article) for article in selected_articles],
            "profile_used": asdict(self.profile),
            "sources_scraped": list(RSS_SOURCES.keys()),
            "scraping_stats": self.scraping_stats,
            "v3_scoring_applied": True,
            "selection_method": "V3 proven system + LLM diversity",
            "quality_metrics": {
                "avg_v3_score": avg_v3_score,
                "min_v3_score": min_v3_score,
                "max_v3_score": max_v3_score,
                "threshold_used": 10.0
            }
        }
        
        # Save with intelligent merging
        await self._intelligent_data_persistence(current_run_data, selected_articles)
        
        return current_run_data
    
    async def _intelligent_data_persistence(self, run_data: Dict, new_articles: List[ArticleData]) -> None:
        """
        INTELLIGENT DATA PERSISTENCE - World's best scraper deserves world's best data handling!
        
        Rules:
        1. NEVER overwrite good data
        2. ALWAYS merge intelligently 
        3. PRESERVE quality improvements
        4. TRACK all runs for debugging
        5. DEDUPLICATE by hash but keep highest quality version
        """
        from pathlib import Path
        import json
        
        data_dir = Path('ai_engine_v5/data')
        data_dir.mkdir(parents=True, exist_ok=True)
        data_file = data_dir / 'scraper_data.json'
        
        # Load existing data
        if data_file.exists():
            try:
                existing_data = json.loads(data_file.read_text(encoding='utf-8'))
            except Exception as e:
                logger.error(f"Failed to load existing data: {e} - starting fresh")
                existing_data = self._create_empty_data_structure()
        else:
            existing_data = self._create_empty_data_structure()
            logger.info("📝 Creating new scraper data file")
        
        # Get current hour key for organization
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        hour_key = current_hour.isoformat()
        
        logger.info(f"💾 Intelligent persistence for hour: {hour_key}")
        
        # Step 1: Always add to run history (for debugging and analysis)
        existing_data["run_history"].append(run_data)
        existing_data["total_runs"] += 1
        
        # Step 2: Intelligent article merging for current hour
        current_hour_data = None
        for hour_data in existing_data["active_articles"]:
            if hour_data["hour"] == hour_key:
                current_hour_data = hour_data
                break
        
        if current_hour_data is None:
            # First run for this hour - add new data
            logger.info("📅 First run for this hour - adding new articles")
            hour_data = {
                "hour": hour_key,
                "articles": [asdict(article) for article in new_articles],
                "processed_by_website": False,
                "runs_count": 1,
                "last_updated": run_data["timestamp"],
                "quality_history": [run_data["quality_metrics"]],
                "best_avg_score": run_data["quality_metrics"]["avg_v3_score"],
                "improvement_log": ["Initial scrape"]
            }
            existing_data["active_articles"].append(hour_data)
            
        else:
            # Multiple runs for same hour - INTELLIGENT MERGE
            logger.info(f"🔄 Multiple runs for hour {hour_key} - applying intelligent merge...")
            
            # Compare quality metrics
            old_avg = current_hour_data["best_avg_score"]
            new_avg = run_data["quality_metrics"]["avg_v3_score"]
            
            # Merge articles intelligently by hash_id, keeping highest scoring version
            existing_articles = {art["hash_id"]: art for art in current_hour_data["articles"]}
            new_articles_dict = {asdict(art)["hash_id"]: asdict(art) for art in new_articles}
            
            merged_articles = {}
            improvements_count = 0
            additions_count = 0
            
            # Process existing articles
            for hash_id, existing_art in existing_articles.items():
                if hash_id in new_articles_dict:
                    new_art = new_articles_dict[hash_id]
                    # Keep the higher scoring version
                    if new_art["total_score"] > existing_art["total_score"]:
                        merged_articles[hash_id] = new_art
                        improvements_count += 1
                        logger.debug(f"📈 Improved: {existing_art['title'][:40]}... ({existing_art['total_score']:.1f} → {new_art['total_score']:.1f})")
                    else:
                        merged_articles[hash_id] = existing_art
                else:
                    # Keep existing article that wasn't found in new run
                    merged_articles[hash_id] = existing_art
            
            # Add completely new articles
            for hash_id, new_art in new_articles_dict.items():
                if hash_id not in existing_articles:
                    merged_articles[hash_id] = new_art
                    additions_count += 1
                    logger.debug(f"➕ New article: {new_art['title'][:40]}...")
                    
            # Update hour data with merged results
            current_hour_data["articles"] = list(merged_articles.values())
            current_hour_data["runs_count"] += 1
            current_hour_data["last_updated"] = run_data["timestamp"]
            current_hour_data["quality_history"].append(run_data["quality_metrics"])
            current_hour_data["best_avg_score"] = max(old_avg, new_avg)
            
            # Track improvement log
            if improvements_count > 0 or additions_count > 0:
                improvement_msg = f"Run {current_hour_data['runs_count']}: "
                if improvements_count > 0:
                    improvement_msg += f"{improvements_count} improved"
                if additions_count > 0:
                    if improvements_count > 0:
                        improvement_msg += f", {additions_count} added"
                    else:
                        improvement_msg += f"{additions_count} added"
                if new_avg > old_avg:
                    improvement_msg += f" (avg score: {old_avg:.1f} → {new_avg:.1f})"
                current_hour_data["improvement_log"].append(improvement_msg)
                logger.info(f"✨ QUALITY IMPROVEMENT: {improvement_msg}")
            else:
                current_hour_data["improvement_log"].append(f"Run {current_hour_data['runs_count']}: No improvements")
                logger.info("📊 No quality improvements this run")
        
        # Step 3: Cleanup old data (keep last 48 hours of active articles)
        if len(existing_data["active_articles"]) > 48:
            existing_data["active_articles"] = existing_data["active_articles"][-48:]
            logger.debug("🧹 Cleaned up old active articles (kept last 48 hours)")
        
        # Step 4: Cleanup run history (keep last 100 runs)
        if len(existing_data["run_history"]) > 100:
            existing_data["run_history"] = existing_data["run_history"][-100:]
            logger.debug("🧹 Cleaned up old run history (kept last 100 runs)")
        
        # Step 5: Update metadata
        existing_data["metadata"]["last_updated"] = run_data["timestamp"]
        existing_data["metadata"]["last_avg_score"] = run_data["quality_metrics"]["avg_v3_score"]
        
        # Step 6: Save atomically (write to temp file first, then rename)
        temp_file = data_file.with_suffix('.tmp')
        try:
            temp_file.write_text(json.dumps(existing_data, indent=2, ensure_ascii=False), encoding='utf-8')
            temp_file.rename(data_file)
            logger.info(f"💾 Data saved with intelligent merging: {data_file}")
            
            # Log final statistics
            total_active_articles = sum(len(h["articles"]) for h in existing_data["active_articles"])
            logger.info(f"📊 Final stats: {len(existing_data['active_articles'])} active hours, {total_active_articles} total articles")
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            if temp_file.exists():
                temp_file.unlink()
    
    def _create_empty_data_structure(self) -> Dict:
        """Create empty data structure for new scraper data file"""
        return {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": "",
                "data_version": "v5_intelligent_persistence",
                "scraper_version": "Rony World's Best Scraper v1.0",
                "last_avg_score": 0.0
            },
            "active_articles": [],  # Articles ready for website processing
            "run_history": [],      # All runs for analysis and debugging
            "total_runs": 0
        }

# Convenience function for single-use
async def run_autonomous_scraper(api_key: str, profile_data: Optional[Dict] = None) -> Dict:
    """Run Rony's autonomous scraping cycle with V3's proven scoring"""
    profile = None
    if profile_data:
        profile = UserProfile.from_json(profile_data)
    
    async with AutonomousScraper(api_key, profile) as scraper:
        return await scraper.run_autonomous_cycle() 