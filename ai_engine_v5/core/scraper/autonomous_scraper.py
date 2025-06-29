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

<<<<<<< Updated upstream
# Import V3's proven scoring system
HIGH_RELEVANCE_KEYWORDS = [
    # Visas & immigration
=======
# HFLLA: 6 Balanced Categories - NEWS IMPORTANCE FIRST with International Perspective
LEARNING_CATEGORIES = {
    "french_life_essentials": {
        "keywords": ["visa", "titre de séjour", "loyer", "caf", "logement", "bail", "assurance", 
                    "impôts", "taxes", "administration", "préfecture", "mairie", "papiers",
                    "travail", "smic", "salaire", "cotisations", "chômage", "pôle emploi",
                    # International life essentials
                    "immigration", "étranger", "expatrié", "naturalisation", "réfugiés"],
        "target_percentage": 16.7,
        "description": "Housing, work, admin, bureaucracy (French + international perspective)"
    },
    "current_affairs": {
        "keywords": ["politique", "gouvernement", "ministère", "élections", "économie", 
                    "inflation", "budget", "france", "actualité", "breaking", "urgent", 
                    "annonce", "décision", "réforme",
                                         # INTERNATIONAL CURRENT AFFAIRS - Critical for global awareness
                     "international", "monde", "global", "europe", "union européenne", "ue",
                     "états-unis", "chine", "russie", # Major powers
                     "guerre", "conflit", "crise", "sanctions", "diplomatie", "sommet",
                     "onu", "otan", "g7", "g20", "accord", "traité"],
        "target_percentage": 16.7,
        "description": "Politics, economics, breaking news (French + international)"
    },
    "culture_society": {
        "keywords": ["culture", "cinéma", "théâtre", "musique", "art", "exposition", "festival",
                    "livre", "littérature", "mode", "société", "social", "tendance", "lifestyle",
                    "célébrité", "people", "spectacle", "divertissement",
                    # International cultural perspective
                    "francophonie", "français à l'étranger", "culture française"],
        "target_percentage": 16.7,
        "description": "Arts, entertainment, social trends (French + international)"
    },
    "sports_recreation": {
        "keywords": ["sport", "football", "rugby", "tennis", "olympiques", "jeux", "équipe",
                    "match", "championnat", "loisirs", "vacances", "tourisme", "voyage",
                    "restaurant", "sortie", "weekend",
                    # International sports
                    "coupe du monde", "euro", "international", "mondial"],
        "target_percentage": 16.7,
        "description": "Sports, leisure, recreation (including international competitions)"
    },
    "innovation_health": {
        "keywords": ["technologie", "tech", "innovation", "numérique", "digital", "intelligence artificielle",
                    "santé", "médecine", "recherche", "science", "environnement", "climat",
                    "énergie", "écologie", "startup", "application",
                    # Global innovation and health
                    "pandémie", "climat mondial", "tech mondiale", "recherche internationale"],
        "target_percentage": 16.7,
        "description": "Technology, science, health, environment (global perspective)"
    },
    "local_regional": {
        "keywords": ["transport", "sncf", "ratp", "métro", "bus", "trafic", "grève",
                    "région", "ville", "municipal", "local", "quartier", "arrondissement",
                    "événement", "manifestation",
                    # European/international regional
                    "europe", "européen", "franco-allemand", "franco-italien"], 
        "target_percentage": 16.7,
        "description": "Local/regional news, transport, European cooperation"
    }
}

# Enhanced keyword system - NEWS IMPORTANCE FIRST with international coverage
HIGH_RELEVANCE_KEYWORDS = [
    # INTERNATIONAL & GLOBAL NEWS - Critical for staying informed
    "international", "monde", "global", "planète", "breaking", "urgent", "alerte",
    "guerre", "conflit", "crise", "sanctions", "accord", "traité",
    "europe", "union européenne", "ue", "bruxelles", "parlement européen",
    "états-unis", "usa", "chine", "russie", # Major powers (stable)
    "onu", "otan", "g7", "g20", "sommet", "diplomatie",
    
    # FRENCH DOMESTIC - Essential French life
>>>>>>> Stashed changes
    "visa", "titre de séjour", "carte de séjour", "naturalisation", "immigration", "étranger",
    # Work & salary
    "smic", "salaire", "cotisations", "travail", "code du travail", "congé", "prélèvement à la source",
    # Housing & cost of living
    "loyer", "caf", "APL", "logement", "bail", "pouvoir d'achat",
    # Transport strikes / SNCF / RATP
    "grève", "SNCF", "RATP", "trafic", "panne",
    # Health & social security
    "sécurité sociale", "ameli", "mutuelle", "assurance maladie",
<<<<<<< Updated upstream
    # Civic & daily-life topics that matter to any resident of France
    "france", "politique", "économie", "justice", "santé", "écologie",
    # Day-to-day admin & services
    "assurance habitation", "ram", "carte vitale", "taxe d'habitation",
    "mutuelle étudiante", "doctolib", "carte navigo",
=======
    "france", "politique", "économie", "justice", "gouvernement",
    "assurance habitation", "carte vitale", "taxe d'habitation", "doctolib", "carte navigo",
>>>>>>> Stashed changes
]

MEDIUM_RELEVANCE_KEYWORDS = [
    # Global issues affecting France
    "climat", "environnement", "pandémie", "migration", "réfugiés", "droits humains",
    "commerce international", "économie mondiale", "inflation mondiale",
    # French domestic medium priority
    "retraite", "impôts", "URSSAF", "CAF", "énergie", "inflation", "prix", "taxe foncière",
    "olympiques", "jeux olympiques", "élections", "météo", "météo-extrême",
    "grève nationale", "canicule", "tempête", "sécheresse",
]

# INTERNATIONAL NEWS PRIORITY - Sources that provide global perspective
INTERNATIONAL_SOURCE_WEIGHTS = {
    "Courrier International": 1.3,  # Specializes in international news
    "France 24": 1.2,               # International French perspective  
    "RFI": 1.2,                     # Radio France Internationale
    "Euronews France": 1.1,         # European perspective
    "TV5 Monde": 1.1,               # Global French-speaking perspective
    "Le Monde": 1.1,                # Quality international coverage
}

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
        
<<<<<<< Updated upstream
        logger.info(f"🤖 Rony initialized with {len(self.high_kw)} high-relevance + {len(self.medium_kw)} medium-relevance keywords")
        logger.info(f"👤 Profile: {len(self.profile_kw)} custom keywords, level={self.profile.french_level}")
=======
        logger.info(f"🤖 Rony initialized with ENHANCED HFLLA (NEWS IMPORTANCE FIRST + Global Awareness)")
        logger.info(f"   🌍 Mission: Most important news (French 60% + International 40%)")
        logger.info(f"   📊 Keywords: {len(self.high_kw)} high + {len(self.medium_kw)} medium (international priority)")
        logger.info(f"   👤 Profile: {profile.french_level} level, lives in {profile.lives_in}")
        logger.info(f"   🎯 Pain points: {profile.pain_points}")
        logger.info(f"   💼 Work domains: {profile.work_domains}")
        logger.info(f"   🧠 LLM: Gemini 2.5 Pro (news importance + learning optimization)")
        logger.info(f"   ✅ Anti-bubble system: Global events prioritized over category balance")
>>>>>>> Stashed changes
        
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
    
<<<<<<< Updated upstream
    def _calculate_v3_score(self, article: ArticleData) -> ArticleData:
        """Calculate V3-style scores for article"""
=======
    def _score_global_importance(self, article: ArticleData) -> float:
        """NEW: Score based on global news importance - preventing French bubble"""
        full_text = f"{article.title} {article.summary}".lower()
        score = 0
        
        # BREAKING NEWS / CRISIS - Highest priority (+6)
        breaking_keywords = ["breaking", "urgent", "alerte", "dernière minute", "flash"]
        crisis_keywords = ["guerre", "conflit", "crise", "urgence", "catastrophe", "attentat"]
        if any(kw in full_text for kw in breaking_keywords + crisis_keywords):
            score += 6
            logger.debug(f"Breaking/Crisis news boost: {article.title[:30]}...")
        
        # MAJOR WORLD EVENTS - Critical for global awareness (+5)
        # Generic patterns for any major world events
        major_world_patterns = ["chine", "états-unis", "russie", "guerre", "conflit armé", 
                               "invasion", "bombardement", "cessez-le-feu", "négociations"]
        if any(kw in full_text for kw in major_world_patterns):
            score += 5
            logger.debug(f"Major world event boost: {article.title[:30]}...")
        
        # INTERNATIONAL POLITICS/ECONOMY - Important for understanding (+4)
        international_affairs = ["onu", "otan", "g7", "g20", "sommet", "diplomatie", 
                               "sanctions", "accord", "traité", "union européenne"]
        if any(kw in full_text for kw in international_affairs):
            score += 4
            logger.debug(f"International affairs boost: {article.title[:30]}...")
        
        # GLOBAL ISSUES affecting France (+3)
        global_issues = ["climat", "pandémie", "commerce international", "migration",
                        "économie mondiale", "inflation mondiale"]
        if any(kw in full_text for kw in global_issues):
            score += 3
            logger.debug(f"Global issues boost: {article.title[:30]}...")
        
        # EUROPEAN NEWS - Important for French context (+2) 
        european_kw = ["europe", "européen", "bruxelles", "parlement européen"]
        if any(kw in full_text for kw in european_kw):
            score += 2
            logger.debug(f"European context boost: {article.title[:30]}...")
        
        return min(score, 8.0)  # Cap at 8.0
    
    def _get_international_source_boost(self, source_name: str) -> float:
        """NEW: Boost international sources for better global coverage"""
        return INTERNATIONAL_SOURCE_WEIGHTS.get(source_name, 1.0)
    
    def _calculate_hflla_score(self, article: ArticleData) -> ArticleData:
        """ENHANCED HFLLA: NEWS IMPORTANCE FIRST + French learning optimization"""
>>>>>>> Stashed changes
        full_text = f"{article.title} {article.summary}"
        
        relevance = self._score_relevance(full_text)
        practical = self._score_practical(full_text)
        newsworthiness = self._score_newsworthiness(article)
        
<<<<<<< Updated upstream
        # Apply V3's weights
        total = (relevance * CURATOR_WEIGHTS["relevance"] + 
                practical * CURATOR_WEIGHTS["practical"] + 
                newsworthiness * CURATOR_WEIGHTS["newsworthiness"])
        
        article.relevance_score = relevance
        article.practical_score = practical
        article.newsworthiness_score = newsworthiness
        article.total_score = total
        
        logger.debug(f"V3 scoring - {article.title[:50]}... = R:{relevance:.1f} P:{practical:.1f} N:{newsworthiness:.1f} TOTAL:{total:.1f}")
=======
        # NEW: Global importance scoring - prioritize important news
        global_importance = self._score_global_importance(article)
        
        # NEW: International source boost
        source_boost = self._get_international_source_boost(article.source)
        
        # Enhanced HFLLA weights - NEWS IMPORTANCE FIRST
        base_total = (relevance * CURATOR_WEIGHTS["relevance"] + 
                     practical * CURATOR_WEIGHTS["practical"] + 
                     newsworthiness * CURATOR_WEIGHTS["newsworthiness"] +
                     category_fit * CURATOR_WEIGHTS["category_bonus"] +
                     profile_fit * CURATOR_WEIGHTS["profile_bonus"])
        
        # Apply global importance boost (up to +8 points)
        total_with_global = base_total + global_importance
        
        # Apply international source boost (1.0x to 1.3x multiplier)
        final_total = total_with_global * source_boost
        
        # Store all scores including new ones
        article.relevance_score = relevance
        article.practical_score = practical
        article.newsworthiness_score = newsworthiness
        article.category_score = category_fit
        article.profile_score = profile_fit
        article.total_score = final_total
        
        # Enhanced logging for debugging
        if global_importance > 0 or source_boost > 1.0:
            logger.debug(f"ENHANCED scoring - {article.title[:30]}... = Base:{base_total:.1f} +Global:{global_importance:.1f} ×Source:{source_boost:.1f} = {final_total:.1f} [{article.predicted_category}]")
        else:
            logger.debug(f"Standard scoring - {article.title[:30]}... = {final_total:.1f} [{article.predicted_category}]")
>>>>>>> Stashed changes
        
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
            
<<<<<<< Updated upstream
            prompt = f"""You are selecting the FINAL 10 articles from {len(top_candidates)} that already passed V3's proven quality scoring system.

{profile_context}

These articles all scored ≥{MIN_SCORE_THRESHOLD} on V3's proven relevance system. Your job is to select the 10 most diverse and profile-relevant articles.

Focus on:
1. Topic diversity (avoid 5 articles about same event)
2. Profile relevance for this specific user
3. Mix of importance levels (some breaking news, some practical advice)
4. Geographic relevance ({self.profile.lives_in or 'France'})
=======
            # Show category distribution to LLM
            category_breakdown = "\n".join([f"   • {cat}: {count} articles" for cat, count in category_counts.items()])
            
            prompt = f"""You are an expert news curator for French learners living in a GLOBALIZED WORLD. Your mission is to select the 10 MOST IMPORTANT news stories of the hour, ensuring learners stay informed about both France and the world without living in a bubble.

{profile_context}

🌍 CORE PRINCIPLE: IMPORTANT NEWS FIRST, then optimize for French learning
Don't let learners miss major world events - they need global awareness to thrive in modern France.

ENHANCED SELECTION FRAMEWORK - Follow these steps:

STEP 1 - NEWS IMPORTANCE ANALYSIS (PRIORITY #1):
Rank articles by genuine global significance:
📢 BREAKING NEWS: Major events happening NOW (wars, crises, disasters)
🌍 WORLD IMPACT: Stories affecting millions globally (wars, major conflicts, superpower relations)
🇪🇺 EUROPEAN AFFAIRS: EU decisions impacting France and French speakers
🇫🇷 FRENCH DOMESTIC: Major French political/economic developments
💥 TRENDING: What the world is discussing today

CRITICAL: If major world events are happening, they MUST be included regardless of category balance.

STEP 2 - INTERNATIONAL/DOMESTIC BALANCE:
Target news distribution:
- French domestic affairs: 60-70% 
- International news (French perspective): 30-40%
- Ensure NO major world events are missed

STEP 3 - CATEGORY DISTRIBUTION:
Current article distribution across 6 HFLLA categories:
{category_breakdown}

🏠 French Life Essentials (16.7%): Housing, work, admin + immigration, international students
🗳️ Current Affairs (16.7%): French politics + INTERNATIONAL politics, global economy  
🎭 Culture & Society (16.7%): French culture + francophonie, international cultural exchange
⚽ Sports & Recreation (16.7%): French sports + international competitions
💡 Innovation & Health (16.7%): French tech/science + global innovations affecting France
📍 Local & Regional (16.7%): {self.profile.lives_in or 'France'} + European cooperation

STEP 4 - FRENCH LEARNING OPTIMIZATION:
After selecting important news, optimize for {self.profile.french_level} level:
- Clear, accessible French vocabulary
- Cultural context for international events
- Pain point relevance: {', '.join(self.profile.pain_points) if self.profile.pain_points else 'General interest'}
- How world events are discussed in French media

STEP 5 - SELECTION VALIDATION:
Verify your selection achieves:
✓ Major world events covered (if any happening)
✓ International perspective: 30-40% of selection
✓ Category balance (4-6 categories ideally)
✓ High HFLLA scores (prefer ≥12.0)
✓ No French bubble - global awareness maintained
>>>>>>> Stashed changes

PRE-SCORED ARTICLES (prioritized by news importance + HFLLA scores):
{chr(10).join(article_summaries)}

<<<<<<< Updated upstream
Respond with ONLY the numbers of the 10 best articles for this user, separated by commas.
Example: 1,3,7,12,15,18,22,25,28,30"""
=======
STEP 6 - FINAL OUTPUT:
Provide your selection as:
SELECTED: [10 numbers separated by commas]
BALANCE: [international vs domestic ratio + category distribution]  
REASONING: [explain news importance decisions + learning optimization]

Example format:
SELECTED: 1,3,7,12,15,18,22,25,28,30
BALANCE: International:4, Domestic:6 | current_affairs:3, french_life:2, culture:2, innovation:2, local:1  
REASONING: Prioritized major international developments and EU trade policies (global importance) alongside French housing reforms and Paris transport strikes. Ensured 40% international coverage to prevent French bubble while addressing user's CAF and logement pain points."""
>>>>>>> Stashed changes

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
        
<<<<<<< Updated upstream
        logger.info(f"🎉 Rony completed autonomous cycle in {duration:.1f}s")
        logger.info(f"   📊 Selection: {len(all_articles)} → {len(selected_articles)} articles")
        logger.info(f"   🎯 V3 Quality: avg={avg_v3_score:.1f}, min={min_v3_score:.1f}, max={max_v3_score:.1f}")
        logger.info(f"   ✅ PROVEN V3 scoring system preserved!")
=======
        logger.info(f"🎉 Rony completed ENHANCED HFLLA cycle in {duration:.1f}s")
        logger.info(f"   📊 Selection: {len(all_articles)} → {len(selected_articles)} articles")
        logger.info(f"   🎯 Enhanced Quality: avg={avg_hflla_score:.1f}, min={min_hflla_score:.1f}, max={max_hflla_score:.1f}")
        if final_category_distribution:
            category_summary = ", ".join([f"{cat}: {count}" for cat, count in final_category_distribution.items()])
            logger.info(f"   🏷️  Categories: {category_summary}")
        logger.info(f"   🧠 Gemini 2.5 Pro: NEWS IMPORTANCE FIRST + learning optimization")
        logger.info(f"   🌍 Global coverage: International sources boosted, crisis events prioritized")
        logger.info(f"   ✅ Anti-bubble system: French learners stay globally informed!")
>>>>>>> Stashed changes
        
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
        
        # Step 1: Add run with processed_by_website flag for workflow compatibility
        run_data["processed_by_website"] = False  # Mark as unprocessed for website workflow
        existing_data["scraper_runs"].append(run_data)
        existing_data["total_runs"] += 1
        
        logger.info(f"✅ Added run to data file (marked as unprocessed)")
        
        # Step 2: Cleanup old runs (keep last 48 runs)
        if len(existing_data["scraper_runs"]) > 48:
            existing_data["scraper_runs"] = existing_data["scraper_runs"][-48:]
            logger.debug("🧹 Kept last 48 runs")
        
        # Step 3: Save atomically (write to temp file first, then rename)
        temp_file = data_file.with_suffix('.tmp')
        try:
            temp_file.write_text(json.dumps(existing_data, indent=2, ensure_ascii=False), encoding='utf-8')
            temp_file.rename(data_file)
            logger.info(f"💾 Data saved successfully: {data_file}")
            logger.info(f"📊 Total runs: {existing_data['total_runs']}, Active runs: {len(existing_data['scraper_runs'])}")
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            if temp_file.exists():
                temp_file.unlink()
    
    def _create_empty_data_structure(self) -> Dict:
        """Create empty data structure for new scraper data file"""
        return {
            "scraper_runs": [],      # All runs for analysis and debugging
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